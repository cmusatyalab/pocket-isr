/*
 * gather_free_space - Collect free disk space into a device-mapper node
 *
 * Copyright (C) 2009-2010 Carnegie Mellon University
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of version 2 of the GNU General Public License as published
 * by the Free Software Foundation.  A copy of the GNU General Public License
 * should have been distributed along with this program in the file
 * COPYING.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
 * for more details.
 */

#include <sys/types.h>
#include <sys/stat.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <stdint.h>
#include <inttypes.h>
#include <unistd.h>
#include <fcntl.h>
#include <libdevmapper.h>
#include <blkid.h>
#include <ext2fs.h>
#include <ntfs/volume.h>
#include <ntfs/attrib.h>
#include <ntfs/bitmap.h>
#include <ntfs/logging.h>
#include <glib.h>

/* Command-line options */
const char **exclude;
unsigned minsize = 4;  /* MiB */
unsigned min_extent_kb;
unsigned max_extent_count = 100000;
gboolean quiet;
gboolean verbose;
gboolean dry_run;

static const GOptionEntry options[] = {
	{"exclude", 'x', 0, G_OPTION_ARG_STRING_ARRAY, &exclude, "Skip the specified device", "DEVICE"},
	{"min", 'm', 0, G_OPTION_ARG_INT, &minsize, "Minimum size for new device", "MiB"},
	{"min-extent-size", 'e', 0, G_OPTION_ARG_INT, &min_extent_kb, "Minimum length of free space extent", "KiB"},
	{"max-extent-count", 'E', 0, G_OPTION_ARG_INT, &max_extent_count, "Maximum number of free space extents", "N"},
	{"test", 't', 0, G_OPTION_ARG_NONE, &dry_run, "Do everything except create the device", NULL},
	{"quiet", 'q', 0, G_OPTION_ARG_NONE, &quiet, "Suppress summary information", NULL},
	{"verbose", 'v', 0, G_OPTION_ARG_NONE, &verbose, "Be verbose", NULL},
	{NULL, 0, 0, 0, NULL, NULL, NULL}
};

/* Other globals */
struct extent *extents;
unsigned used_extents;
unsigned min_extent_sectors;

/* Logging */

static G_GNUC_PRINTF(3, 4) void _log(gboolean do_squash, gboolean do_exit,
			const char *fmt, ...)
{
	va_list ap;

	if (do_squash)
		return;
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	fprintf(stderr, "\n");
	va_end(ap);
	if (do_exit)
		exit(1);
}

#define msg(fmt, args...) _log(!verbose, FALSE, fmt, ## args)
#define info(fmt, args...) _log(quiet, FALSE, fmt, ## args)
#define die(fmt, args...) _log(FALSE, TRUE, fmt, ## args)

static void _dm_log(int level, const char *file, int line, const char *fmt,
			...)
{
	va_list ap;

	(void) file;
	(void) line;

	if (level > 4)
		return;
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	fprintf(stderr, "\n");
	va_end(ap);
}

/* blkid helpers */

struct device {
	GQuark id;
	gchar *path;
	gchar *fstype;
	uint64_t sectors;
	uint64_t free_sectors;
	uint64_t accepted_sectors;
	unsigned free_extents;
	unsigned accepted_extents;
};

static void device_tree_insert(GTree *devices, const char *path,
			const char *fstype)
{
	struct device *device;

	device = g_slice_new0(struct device);
	device->id = g_quark_from_string(path);
	device->path = g_strdup(path);
	device->fstype = g_strdup(fstype);
	g_tree_insert(devices, device->path, device);
}

static void device_free(void *_device)
{
	struct device *device = _device;

	g_free(device->path);
	g_free(device->fstype);
	g_slice_free(struct device, device);
}

static int compare_device_names(const void *a, const void *b, void *data)
{
	(void) data;
	return strcmp(a, b);
}

static GTree *device_tree_new(void)
{
	return g_tree_new_full(compare_device_names, NULL, NULL, device_free);
}

static const char *blkid_dev_get_value(blkid_dev dev, const char *tag)
{
	blkid_tag_iterate iter;
	const char *cur_tag;
	const char *value;
	const char *ret = NULL;

	iter = blkid_tag_iterate_begin(dev);
	while (!blkid_tag_next(iter, &cur_tag, &value)) {
		if (!strcmp(cur_tag, tag)) {
			ret = value;
			break;
		}
	}
	blkid_tag_iterate_end(iter);
	return ret;
}

static void add_all_devices(blkid_cache cache, GTree *devices)
{
	blkid_dev_iterate iter;
	blkid_dev dev;
	const char *path;
	const char *fstype;

	if (blkid_probe_all(cache))
		die("Couldn't probe devices");
	iter = blkid_dev_iterate_begin(cache);
	while (!blkid_dev_next(iter, &dev)) {
		path = blkid_dev_devname(dev);
		fstype = blkid_dev_get_value(dev, "TYPE");
		if (fstype != NULL)
			device_tree_insert(devices, path, fstype);
	}
	blkid_dev_iterate_end(iter);
}

static void add_device(blkid_cache cache, GTree *devices, const char *path)
{
	blkid_dev dev;
	const char *fstype;

	dev = blkid_get_dev(cache, path, BLKID_DEV_NORMAL);
	if (dev == NULL) {
		msg("%s: Couldn't probe device", path);
		return;
	}
	fstype = blkid_dev_get_value(dev, "TYPE");
	if (fstype == NULL) {
		msg("%s: Couldn't determine filesystem type", path);
		return;
	}
	device_tree_insert(devices, path, fstype);
}

/* dm helpers */

struct extent {
	struct device *device;
	uint64_t start_sect;
	uint64_t sect_count;
};

static gboolean dm_device_exists(const char *name)
{
	struct dm_task *dmt;
	struct dm_info info;

	dmt = dm_task_create(DM_DEVICE_INFO);
	if (dmt == NULL)
		die("Couldn't create DM task");
	if (!dm_task_set_name(dmt, name))
		die("Couldn't configure device name");
	if (!dm_task_run(dmt))
		die("Couldn't query device");
	if (!dm_task_get_info(dmt, &info))
		die("Couldn't get device info");
	dm_task_destroy(dmt);
	return info.exists;
}

static void dm_add_extent(struct dm_task *task, struct extent *extent,
			uint64_t offset)
{
	gchar *args;

	args = g_strdup_printf("%s %"PRIu64, extent->device->path,
				extent->start_sect);
	if (!dm_task_add_target(task, offset, extent->sect_count, "linear",
				args))
		die("Couldn't add %"PRIu64" sectors of %s at %"PRIu64
					" to map", extent->sect_count,
					extent->device->path,
					extent->start_sect);
	g_free(args);
}

/* Extent list */

/* The length of the DM table needs to be bounded, since it's just a
   vmalloc'd array in kernel memory, and vmalloc space is generally
   limited to 128 MiB.  We want the table to contain the largest
   available extents, sorted by device and sector number.  (We don't
   want to interleave extents from different devices because they may
   be different partitions on the same physical disk.)

   Algorithm:

   1. Allocate an array of length max_extent_count.
   2. Insert extents into the array in sequential order until the array
      fills up.
   3. If this occurs, convert the array to a binary min-heap based on the
      length of each extent.  Continue inserting extents, but only if they
      are larger than the smallest extent.  Before inserting a new extent,
      remove the smallest extent.
   4. Sort the array by device and sector number and add its entries to a
      DM table.
 */

static void extent_swap(struct extent *a, struct extent *b)
{
	struct extent tmp;

	tmp = *a;
	*a = *b;
	*b = tmp;
}

static void extent_sift_down(unsigned node)
{
	unsigned left = 2 * node + 1;
	unsigned right = 2 * node + 2;
	uint64_t min = extents[node].sect_count;
	unsigned min_node = node;

	if (left < used_extents && extents[left].sect_count < min) {
		min = extents[left].sect_count;
		min_node = left;
	}
	if (right < used_extents && extents[right].sect_count < min) {
		min = extents[right].sect_count;
		min_node = right;
	}
	if (min_node != node) {
		extent_swap(&extents[min_node], &extents[node]);
		extent_sift_down(min_node);
	}
}

static void extent_make_heap(void)
{
	int node;

	for (node = (int) (used_extents / 2) - 1; node >= 0; node--)
		extent_sift_down(node);
}

static void add_extent(struct device *device, uint64_t start_sect,
			uint64_t sect_count)
{
	struct extent new = {
		.device = device,
		.start_sect = start_sect,
		.sect_count = sect_count
	};

	device->free_extents++;
	device->free_sectors += sect_count;
	if (sect_count < min_extent_sectors)
		return;
	if (used_extents < max_extent_count) {
		extents[used_extents] = new;
		if (++used_extents == max_extent_count)
			extent_make_heap();
	} else {
		if (extents[0].sect_count >= sect_count)
			return;
		extents[0].device->accepted_extents--;
		extents[0].device->accepted_sectors -= extents[0].sect_count;
		extents[0] = new;
		extent_sift_down(0);
	}
	device->accepted_extents++;
	device->accepted_sectors += sect_count;
}

static int extent_compare_offsets(const void *_a, const void *_b)
{
	const struct extent *a = _a;
	const struct extent *b = _b;

	if (a->device->id != b->device->id)
		return a->device->id < b->device->id ? -1 : 1;
	if (a->start_sect != b->start_sect)
		return a->start_sect < b->start_sect ? -1 : 1;
	return 0;
}

static void extent_populate_table(struct dm_task *task)
{
	uint64_t sector = 0;
	unsigned n;

	qsort(extents, used_extents, sizeof(*extents), extent_compare_offsets);
	for (n = 0; n < used_extents; n++) {
		dm_add_extent(task, &extents[n], sector);
		sector += extents[n].sect_count;
	}
}

/* ext[234] */

static void handle_ext(struct device *device)
{
	ext2_filsys fs;
	blk_t blk;
	uint64_t run;
	unsigned block_sectors;

	if (ext2fs_open(device->path, 0, 0, 0, unix_io_manager, &fs)) {
		msg("Couldn't read filesystem on %s", device->path);
		return;
	}
	if (fs->super->s_state & EXT2_ERROR_FS) {
		msg("Filesystem on %s has errors, skipping", device->path);
		goto out;
	}
	if (!(fs->super->s_state & EXT2_VALID_FS)) {
		msg("Unclean filesystem on %s, skipping", device->path);
		goto out;
	}
	if (ext2fs_read_block_bitmap(fs)) {
		msg("Couldn't read block bitmap on %s", device->path);
		goto out;
	}
	block_sectors = fs->blocksize / 512;
	for (blk = fs->super->s_first_data_block, run = 0;
				blk < fs->super->s_blocks_count; blk++) {
		if (!ext2fs_fast_test_block_bitmap(fs->block_map, blk)) {
			run++;
		} else if (run) {
			add_extent(device, (blk - run) * block_sectors,
						run * block_sectors);
			run = 0;
		}
	}
	if (run)
		add_extent(device, (blk - run) * block_sectors,
					run * block_sectors);
out:
	if (ext2fs_close(fs))
		die("Couldn't close filesystem on %s", device->path);
}

/* ntfs */

static void handle_ntfs(struct device *device)
{
	ntfs_volume *vol;
	uint8_t *bitmap;
	int64_t bitmap_len;
	int64_t lcn;
	uint64_t run;
	unsigned cluster_sectors;

	if (verbose)
		ntfs_log_set_handler(ntfs_log_handler_stderr);

	/* We ask for a forensic mount so that the volume header won't be
	   updated.  That doesn't guarantee that the filesystem isn't
	   changed at all; we'd also need NTFS_MNT_RDONLY for that.  However,
	   we don't use that flag so that ntfs_mount() will fail the
	   mount if the log is dirty or the filesystem has a Windows
	   hibernate image. */
	vol = ntfs_mount(device->path, NTFS_MNT_FORENSIC);
	if (vol == NULL) {
		msg("Couldn't open filesystem on %s; it may be unclean "
					"or hibernated", device->path);
		return;
	}
	if (ntfs_version_is_supported(vol)) {
		msg("Unsupported filesystem version on %s", device->path);
		goto out;
	}
	if (NVolWasDirty(vol)) {
		msg("Filesystem on %s needs checking, skipping", device->path);
		goto out;
	}
	bitmap_len = vol->lcnbmp_na->data_size;
	if (bitmap_len * 8 < vol->nr_clusters) {
		msg("Unexpectedly short volume bitmap on %s", device->path);
		goto out;
	}
	bitmap = g_malloc(bitmap_len);
	if (ntfs_attr_pread(vol->lcnbmp_na, 0, bitmap_len, bitmap) !=
				bitmap_len) {
		msg("Short read for volume bitmap on %s", device->path);
		g_free(bitmap);
		goto out;
	}
	cluster_sectors = vol->cluster_size / 512;
	for (lcn = 0, run = 0; lcn < vol->nr_clusters; lcn++) {
		if (!ntfs_bit_get(bitmap, lcn)) {
			run++;
		} else if (run) {
			add_extent(device, (lcn - run) * cluster_sectors,
						run * cluster_sectors);
			run = 0;
		}
	}
	if (run)
		add_extent(device, (lcn - run) * cluster_sectors,
					run * cluster_sectors);
	g_free(bitmap);
out:
	if (ntfs_umount(vol, FALSE))
		die("Couldn't close filesystem on %s", device->path);
}

/* swap */

struct swap_header {
	uint8_t bootbits[1024];
	uint32_t version;
	uint32_t last_page;
	uint32_t nr_badpages;
	uint8_t uuid[16];
	uint8_t volume_name[16];
	uint32_t padding[117];
	uint32_t badpages[1];
};

static void handle_swap(struct device *device)
{
	int fd;
	int pagesize;
	unsigned page_sectors;
	char *buf;
	struct swap_header *hdr;

	pagesize = sysconf(_SC_PAGESIZE);
	if (pagesize == -1)
		die("Couldn't get page size");
	buf = g_malloc(pagesize);
	fd = open(device->path, O_RDONLY);
	if (fd == -1) {
		msg("Couldn't open %s", device->path);
		goto out;
	}
	if (read(fd, buf, pagesize) != pagesize) {
		msg("Couldn't read %s", device->path);
		goto out;
	}
	if (memcmp(buf + pagesize - 10, "SWAPSPACE2", 10)) {
		msg("Unrecognized swap signature on device %s", device->path);
		goto out;
	}
	hdr = (struct swap_header *) buf;
	if (hdr->version != 1) {
		msg("Unknown swap version %d on %s", hdr->version,
					device->path);
		goto out;
	}
	if (hdr->nr_badpages) {
		/* Not implemented */
		msg("Rejecting swap device %s with %d bad pages",
					device->path, hdr->nr_badpages);
		goto out;
	}
	/* Sanity check device length */
	page_sectors = pagesize / 512;
	if (hdr->last_page != (device->sectors / page_sectors) - 1) {
		msg("Length mismatch on swap device %s", device->path);
		goto out;
	}
	add_extent(device, page_sectors, ((uint64_t) hdr->last_page) *
				page_sectors);
out:
	g_free(buf);
	close(fd);
}

/* control */

static const struct handler {
	const char *fstype;
	void (*run)(struct device *device);
} handlers[] = {
	{"ext2", handle_ext},
	{"ext3", handle_ext},
	{"ext4", handle_ext},
	{"ntfs", handle_ntfs},
	{"swap", handle_swap},
	{NULL, NULL}
};

static gboolean handle_one(void *path, void *_device, void *data)
{
	struct device *device = _device;
	const struct handler *hdlr;
	const char *reason = NULL;
	int flags;

	(void) path;
	(void) data;

	if (ext2fs_check_if_mounted(device->path, &flags))
		die("Couldn't check mount status of %s", device->path);
	if ((flags & (EXT2_MF_MOUNTED | EXT2_MF_READONLY)) == EXT2_MF_MOUNTED)
		reason = "mounted rw";
	else if (flags & EXT2_MF_SWAP)
		reason = "an active swap device";
	else if (flags & EXT2_MF_BUSY)
		reason = "busy";
	if (reason != NULL) {
		msg("%s is %s, skipping", device->path, reason);
		return FALSE;
	}

	if (ext2fs_get_device_size2(device->path, 512,
				(blk64_t *) &device->sectors)) {
		msg("Couldn't query size of %s", device->path);
		return FALSE;
	}

	for (hdlr = handlers; hdlr->fstype != NULL; hdlr++) {
		if (!strcmp(device->fstype, hdlr->fstype)) {
			msg("%s: Detected %s", device->path, device->fstype);
			hdlr->run(device);
			return FALSE;
		}
	}
	msg("%s: Unknown filesystem %s", device->path, device->fstype);
	return FALSE;
}

static gboolean print_stats(void *path, void *_device, void *_total)
{
	struct device *device = _device;
	uint64_t *total = _total;

	(void) path;

	if (device->free_sectors > 0)
		info("%s (%s): %"PRIu64"/%"PRIu64"/%"PRIu64" MiB, "
				"%u/%u extents",
				device->path, device->fstype,
				device->accepted_sectors >> 11,
				device->free_sectors >> 11,
				device->sectors >> 11,
				device->accepted_extents,
				device->free_extents);
	*total += device->accepted_sectors;
	return FALSE;
}

int main(int argc, char **argv)
{
	GOptionContext *opt_ctx;
	GError *err = NULL;
	const char *device_name;
	blkid_cache blkid_cache;
	GTree *devices;
	struct dm_task *task;
	uint64_t accepted_sectors = 0;

	opt_ctx = g_option_context_new("NODE [DEVICE ...]");
	g_option_context_set_summary(opt_ctx, "Collects free disk space "
				"into a device-mapper node.");
	g_option_context_add_main_entries(opt_ctx, options, NULL);
	if (!g_option_context_parse(opt_ctx, &argc, &argv, &err))
		die("%s", err->message);
	g_option_context_free(opt_ctx);
	min_extent_sectors = min_extent_kb << 1;
	if (max_extent_count == 0)
		die("--max-extent-count must be at least 1.");

	if (argc < 2)
		die("You must specify a device name.");
	device_name = argv[1];
	argc -= 2;
	argv += 2;

	if (geteuid() != 0)
		die("You must be root.");

	extents = g_new(struct extent, max_extent_count);

	dm_log_init(_dm_log);
	if (dm_device_exists(device_name))
		die("Device %s already exists", device_name);

	devices = device_tree_new();
	/* Avoid using a cache file, since we want to ensure we don't get
	   stale data, and if we use a real cache file there's nothing in
	   the API that allows us to detect/reject stale entries. */
	if (blkid_get_cache(&blkid_cache, "/dev/null"))
		die("Couldn't get blkid cache");
	if (argc)
		for (; argc; argc--, argv++)
			add_device(blkid_cache, devices, *argv);
	else
		add_all_devices(blkid_cache, devices);
	if (exclude != NULL)
		for (; *exclude != NULL; exclude++)
			g_tree_remove(devices, *exclude);
	g_tree_foreach(devices, handle_one, NULL);

	g_tree_foreach(devices, print_stats, &accepted_sectors);
	info("Total accepted: %"PRIu64" MiB, %u extents",
				accepted_sectors >> 11, used_extents);
	if (minsize && (accepted_sectors >> 11) < minsize)
		die("Minimum size requirement not met, aborting");

	task = dm_task_create(DM_DEVICE_CREATE);
	if (task == NULL)
		die("Couldn't create DM task");
	if (!dm_task_set_name(task, device_name))
		die("Couldn't set device name");
	extent_populate_table(task);
	if (!dry_run && !dm_task_run(task))
		die("Couldn't create device");
	dm_task_destroy(task);

	g_free(extents);
	blkid_put_cache(blkid_cache);
	g_tree_destroy(devices);

	if (dry_run)
		info("Test mode, not creating device");
	else
		info("Created device %s", device_name);

	return 0;
}
