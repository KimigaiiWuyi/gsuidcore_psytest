from pathlib import Path

from gsuid_core.data_store import get_res_path

psytest_path = get_res_path('psytest')
history_path = get_res_path(['psytest', 'history'])

data_path = Path(__file__).parent / 'test_lib'
all_test = list(data_path.glob('*'))
