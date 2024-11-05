# db_routers.py
class LegacyRouter:
    """
    A router to control database operations on models related to the legacy parts database.
    """

    def db_for_read(self, model, **hints):
        """
        Attempts to read parts models go to the legacy database.
        """
        if model._meta.app_label == 'myapp' and model._meta.model_name == 'part':
            return 'legacy'
        return None

    def db_for_write(self, model, **hints):
        """
        Prevents writes to the legacy database.
        """
        if model._meta.app_label == 'myapp' and model._meta.model_name == 'part':
            return 'legacy'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Disable migrations for the legacy database.
        """
        if db == 'legacy':
            return False
        return None
