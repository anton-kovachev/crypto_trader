import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from botocore.exceptions import ClientError

from database.database import AccountsDatabase


class FakeS3Client:
    def __init__(self, content: bytes | None = None) -> None:
        self.content = content
        self.uploaded: bytes | None = None
        self.read_target: tuple[str, str] | None = None
        self.upload_target: tuple[str, str] | None = None

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, io.BytesIO]:
        self.read_target = (Bucket, Key)
        if self.content is None:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "Object not found"}},
                "GetObject",
            )
        return {"Body": io.BytesIO(self.content)}

    def upload_fileobj(self, file: io.BufferedReader, bucket: str, key: str) -> None:
        self.upload_target = (bucket, key)
        self.uploaded = file.read()


class AccountsDatabaseS3Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_directory.cleanup)
        self.db_path = Path(self.temp_directory.name) / "accounts.db"
        self.s3 = FakeS3Client()

        self.lambda_patch = patch.object(AccountsDatabase, "IS_LAMBDA", True)
        self.path_patch = patch.object(AccountsDatabase, "DB_PATH", self.db_path)
        self.env_patch = patch.dict(
            "os.environ",
            {
                "ACCOUNT_DB_S3_BUCKET": "test-bucket",
                "ACCOUNT_DB_S3_KEY": "test/accounts.db",
            },
        )
        self.client_patch = patch(
            "database.database.boto3.client",
            return_value=self.s3,
        )
        for patcher in (
            self.lambda_patch,
            self.path_patch,
            self.env_patch,
            self.client_patch,
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_loads_existing_s3_database_and_uploads_updated_file(self) -> None:
        self.s3.content = b"existing database"

        AccountsDatabase.load_from_s3()
        self.assertEqual(self.db_path.read_bytes(), b"existing database")
        self.assertEqual(self.s3.read_target, ("test-bucket", "test/accounts.db"))

        self.db_path.write_bytes(b"updated database")
        AccountsDatabase.save_to_s3()

        self.assertEqual(self.s3.uploaded, b"updated database")
        self.assertEqual(self.s3.upload_target, ("test-bucket", "test/accounts.db"))

    def test_missing_s3_object_starts_with_a_new_database(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.write_bytes(b"stale local database")

        AccountsDatabase.load_from_s3()
        self.assertFalse(self.db_path.exists())

        with AccountsDatabase():
            pass
        AccountsDatabase.save_to_s3()

        self.assertTrue(self.s3.uploaded)

    def test_local_mode_does_not_access_s3(self) -> None:
        with (
            patch.object(AccountsDatabase, "IS_LAMBDA", False),
            patch(
                "database.database.boto3.client",
                side_effect=AssertionError("Local mode must not use S3"),
            ),
        ):
            AccountsDatabase.load_from_s3()
            AccountsDatabase.save_to_s3()


if __name__ == "__main__":
    unittest.main()
