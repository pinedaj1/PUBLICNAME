import psycopg2
import requests
from config import config
from time import sleep
from subprocess import Popen, PIPE, DEVNULL
from os import chdir, kill
from signal import SIGINT
from tqdm import tqdm

# spawn server
server = Popen('./run_server.sh', stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL)
chdir('web')
try:
    # wait a bit to let database get online
    sleep(4)

    with psycopg2.connect(**config()) as conn:
        def connect(query):
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()

        all_mno = [row[0] for row in connect('SELECT mno FROM municipality;')]

        def test_get(path):
            if requests.get('http://localhost:5000/' + path).status_code != 200:
                raise RuntimeError('error on path "' + path + '"')

        def test_post(path, data):
            if requests.post('http://localhost:5000/' + path, data).status_code != 200:
                raise RuntimeError('error on path "' + path + '" with data ' + str(data))

        # test root endpoint
        test_get('')

        # test endpoints per municipality
        for mno in tqdm(all_mno):
            # test municipality endpoint
            test_post('municipality', {'mno': mno})
            # test mot endpoint
            test_post('mot', {'mno': mno})
            # if vmt endpoint valid, test vmt endpoint
            if connect(f'SELECT * FROM on_road_vehicle WHERE mno = {mno}'):
                test_post('vmt', {'mno': mno})
            # test ev endpoints
            test_post('ev', {'mno': mno})
finally:
    kill(server.pid, SIGINT)
    server.wait()
