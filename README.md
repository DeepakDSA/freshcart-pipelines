# freshcart-pipelines

Data Engineering assignment "From Git to Gold": version control, ELT, ML pipelines and event streaming.

| Folder | Part | Contents |
| --- | --- | --- |
| `elt/freshcart_elt_assignment.ipynb` | B, Bonus | FreshCart ELT on Snowflake (bronze → silver → gold), B1–B5 and the stream-to-lakehouse bonus |
| `iris_project/` | C | Mage project: `load_iris → prepare_data → {train_model → {save_results, evaluate_model}, train_knn}` |
| `mage_iris_assignment.ipynb` | C | Colab notebook that runs C1–C4 and opens the Mage UI |
| `stream/` | D | RabbitMQ dispatcher and driver scripts |
| `tests/` | A | pytest tests run by CI |
| `.github/workflows/ci.yml` | A | GitHub Actions: runs pytest on every push |

## Running the Mage pipeline (Part C)

```bash
mage run iris_project iris_classifier --test
mage run iris_project iris_classifier --test --runtime-vars '{"max_depth": 2}'
```

## Running the tests

```bash
pip install -r requirements.txt
pytest -v
```

## Running the stream (Part D)

Start a broker (in Colab):

```bash
!apt-get install -y rabbitmq-server
!service rabbitmq-server start
```

Then, from the repo root:

```bash
bash stream/run_demo.sh 120
```

This starts the six drivers from D1, sends one message for each D1 routing key,
then runs the random dispatcher for 120 seconds. Logs go to `stream/logs/`.

To use a hosted broker instead (e.g. CloudAMQP), set `AMQP_URL` in your environment
or in a `.env` file. `.env` is ignored by Git, so the URL never gets committed.

Individual scripts:

```bash
python stream/driver.py Ravi "bangalore.koramangala.*"
python stream/dispatcher.py --duration 120
python stream/dispatcher.py --key bangalore.koramangala.food   # one message, for proofs
```
