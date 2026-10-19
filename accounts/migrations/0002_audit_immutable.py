from django.db import migrations


def add_mysql_triggers(apps, schema_editor):
    if schema_editor.connection.vendor == "sqlite":
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("DROP TRIGGER IF EXISTS srs_audit_no_update")
            cursor.execute("DROP TRIGGER IF EXISTS srs_audit_no_delete")
            cursor.execute("CREATE TRIGGER srs_audit_no_update BEFORE UPDATE ON accounts_auditlog BEGIN SELECT RAISE(ABORT, 'Audit log is append-only'); END")
            cursor.execute("CREATE TRIGGER srs_audit_no_delete BEFORE DELETE ON accounts_auditlog BEGIN SELECT RAISE(ABORT, 'Audit log is append-only'); END")
        return
    if schema_editor.connection.vendor != "mysql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TRIGGER IF EXISTS srs_audit_no_update")
        cursor.execute("DROP TRIGGER IF EXISTS srs_audit_no_delete")
        cursor.execute("CREATE TRIGGER srs_audit_no_update BEFORE UPDATE ON accounts_auditlog FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audit log is append-only'")
        cursor.execute("CREATE TRIGGER srs_audit_no_delete BEFORE DELETE ON accounts_auditlog FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Audit log is append-only'")


def remove_mysql_triggers(apps, schema_editor):
    if schema_editor.connection.vendor not in {"mysql", "sqlite"}:
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP TRIGGER IF EXISTS srs_audit_no_update")
        cursor.execute("DROP TRIGGER IF EXISTS srs_audit_no_delete")


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.RunPython(add_mysql_triggers, remove_mysql_triggers)]
