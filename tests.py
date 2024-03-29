import contextlib
import io
import os
import tempfile
import logging

import pytest
import machine
import translator


@pytest.mark.golden_test("tests/golden_test/hello.yml")
def test_hello_program(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        source = os.path.join(tmp_dir_name, "hello_test.js")
        target = os.path.join(tmp_dir_name, "hello.out")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden['source'])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target])
            machine.main([target, ''])

        with open(target, encoding="utf-8") as file:
            code = file.read()

        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        assert caplog.text == golden["log"]


@pytest.mark.golden_test("tests/golden_test/cat.yml")
def test_cat_program(golden, caplog):
    caplog.set_level(logging.DEBUG)

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        source = os.path.join(tmp_dir_name, "cat_test.js")
        input_stream = os.path.join(tmp_dir_name, "privet_input.txt")
        target = os.path.join(tmp_dir_name, "cat.out")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden['source'])

        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden['input'])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target])
            machine.main([target, input_stream])

        with open(target, encoding="utf-8") as file:
            code = file.read()

        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]
        assert caplog.text == golden["log"]


@pytest.mark.golden_test("tests/golden_test/prob5.yml")
def test_prob5_program(golden):
    with tempfile.TemporaryDirectory() as tmp_dir_name:
        source = os.path.join(tmp_dir_name, "prob5_test.js")
        target = os.path.join(tmp_dir_name, "prob5.out")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden['source'])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main([source, target])
            machine.main([target, ''])

        with open(target, encoding="utf-8") as file:
            code = file.read()

        assert code == golden.out["code"]
        assert stdout.getvalue() == golden.out["output"]