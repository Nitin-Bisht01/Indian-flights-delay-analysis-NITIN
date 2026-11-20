# Flight Operations & Delay Intelligence Dashboard

## Files
- `app.py` — upgraded Streamlit dashboard
- `india_flight_delay_model_input.csv` — supplied dataset, renamed to the filename expected by the app
- `requirements.txt` — Python dependencies

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy / update on Streamlit Community Cloud
1. Download and extract this ZIP.
2. In the GitHub repository connected to your Streamlit app, replace the existing `app.py`.
3. Add or replace `requirements.txt`.
4. Add `india_flight_delay_model_input.csv` to the same repository folder as `app.py`.
5. Commit and push the changes. Streamlit Community Cloud should redeploy automatically.
6. If deployment does not start, open the app's Manage app page and reboot it.

The dashboard also supports uploading a CSV from its sidebar. The expected columns are the columns in the supplied project dataset.

## Important interpretation note
`Delay_Target` is treated as the dataset's delayed/not-delayed label. The dashboard describes observed patterns; it does not provide live flight status or causal conclusions.
