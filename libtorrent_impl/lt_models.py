import peewee

LT_DB = peewee.Proxy()


class Torrent(peewee.Model):
    info_hash = peewee.CharField(max_length=40, unique=True)
    torrent_file = peewee.BlobField()
    download_path = peewee.TextField()
    name = peewee.TextField(null=True)
    resume_data = peewee.BlobField(null=True)

    class Meta:
        database = LT_DB


class Migration(peewee.Model):
    name = peewee.CharField(max_length=256)

    class Meta:
        database = LT_DB


LT_MODELS = [
    Torrent,
    Migration,
]

LT_MIGRATIONS = [
    ('0001_initial', lambda: None),
]
