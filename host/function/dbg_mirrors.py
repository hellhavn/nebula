from host import FileNode
from host.models.Cloud import Cloud

__author__ = 'zadjii'


def dbg_mirrors(instance, argv):
    db = instance.get_db()
    mirrors = db.session.query(Cloud).all()
    for mirror in mirrors:
        print(
            '[{:3}]\t{}/{}, {}, {}, {}\n\t{}'
            .format(
                mirror.id
                , mirror.username
                , mirror.name
                , mirror.created_on
                , mirror.last_update
                , mirror.completed_mirroring
                , [child.name for child in mirror.children.all()]
            )
        )

