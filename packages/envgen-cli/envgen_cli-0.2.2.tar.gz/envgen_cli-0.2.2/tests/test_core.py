import os
import tempfile
from envgen.core import EnvFileGenerator


def test_parse_template():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("# Comment\n")
        f.write("\n")
        f.write("KEY1=value1\n")
        f.write("KEY2=\n")
        f.write("KEY3\n")  # invalid
        f.write("KEY4 = spaced_value \n")
        template_path = f.name

    try:
        generator = EnvFileGenerator(template_path=template_path)
        entries = generator.parse_template()

        assert len(entries) == 3
        assert entries[0] == ("KEY1", "value1")
        assert entries[1] == ("KEY2", None)
        assert entries[2] == ("KEY4", "spaced_value")
    finally:
        os.unlink(template_path)


def test_generate_and_write():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("DB_NAME=\n")
        f.write("API_KEY=secret123\n")
        template_path = f.name

    output_path = template_path + ".out"

    try:
        generator = EnvFileGenerator(template_path=template_path, output_path=output_path)

        # Mock user input
        def mock_prompt(key: str, default: Optional[str] = None) -> str:
            return "mydb" if key == "DB_NAME" else (default or "")

        generator.prompt_user = mock_prompt  # type: ignore

        data = generator.generate_env(force=True)
        generator.write_env_file(data)

        assert data["DB_NAME"] == "mydb"
        assert data["API_KEY"] == "secret123"

        with open(output_path, "r") as f:
            content = f.read()
            assert "DB_NAME=mydb\n" in content
            assert "API_KEY=secret123\n" in content

    finally:
        os.unlink(template_path)
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_generate_password():
    generator = EnvFileGenerator()
    pwd = generator.generate_password(16)
    assert len(pwd) == 16
    assert any(c.isupper() for c in pwd)
    assert any(c.islower() for c in pwd)
    assert any(c.isdigit() for c in pwd)