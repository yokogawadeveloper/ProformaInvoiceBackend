SECOND_EXTERNAL_APPS = [
    'excelupload',
    'orderack',
    'masterdata',
    'users'
]


class SecondExternalDBRouter(object):
    def db_for_read(self, model, **hints):
        if model._meta.app_label in SECOND_EXTERNAL_APPS:
            return 'backup'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in SECOND_EXTERNAL_APPS:
            return 'backup'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label in SECOND_EXTERNAL_APPS or \
                obj2._meta.app_label in SECOND_EXTERNAL_APPS:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in SECOND_EXTERNAL_APPS:
            return db == 'backup'
        else:
            return db == 'backup'

