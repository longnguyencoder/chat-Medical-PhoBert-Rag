@echo off
python -u evaluation\evaluate_model.py --test_file evaluation\test_data\auto_detect_test.csv > eval_output.txt 2>&1
type eval_output.txt
