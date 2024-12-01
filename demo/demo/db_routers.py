# # db_routers.py
# class LegacyRouter:
#     """
#     A router to control database operations on models related to the legacy parts database.
#     """
#
#     def db_for_read(self, model, **hints):
#         """
#         Attempts to read parts models go to the legacy database.
#         """
#         if model._meta.app_label == 'myapp' and model._meta.model_name == 'part':
#             return 'legacy'
#         return None
#
#     def db_for_write(self, model, **hints):
#         """
#         Prevents writes to the legacy database.
#         """
#         if model._meta.app_label == 'myapp' and model._meta.model_name == 'part':
#             return 'legacy'
#         return None
#
#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         """
#         Disable migrations for the legacy database.
#         """
#         if db == 'legacy':
#             return False
#         return None
#

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
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Writes for the parts model should go to the legacy database.
        """
        if model._meta.app_label == 'myapp' and model._meta.model_name == 'part':
            return 'legacy'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both models are in the same app or if one is from the 'legacy' database.
        """
        if (
            obj1._meta.app_label == 'myapp' and
            obj2._meta.app_label == 'myapp'
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Disable migrations for the legacy database.
        """
        if db == 'legacy':
            return False
        return db == 'default'
