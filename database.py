# database.py - Updated for Pandas 3.0 & InfluxDB _time mapping
import config
import pandas as pd
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS


def get_db_client():
    try:
        client = InfluxDBClient(url=config.DB_URL, token=config.DB_TOKEN, org=config.DB_ORG)
        return client
    except Exception as e:
        print(f"Error connecting to InfluxDB: {e}")
        return None


def _rename_and_format_df(df, tag_map):
    if df.empty: return df

    # 1. Drop internal Influx columns
    cols_to_drop = ['result', 'table', '_start', '_stop', '_measurement']
    df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

    # 2. RENAME _time to config.TIMESTAMP_COLUMN before any operations
    if '_time' in df.columns:
        df = df.rename(columns={'_time': config.TIMESTAMP_COLUMN})

    # 3. Pivot if necessary
    if '_field' in df.columns and '_value' in df.columns:
        df = df.pivot_table(index=config.TIMESTAMP_COLUMN, columns='_field', values='_value').reset_index()

    # 4. Apply User Tag Mapping
    df = df.rename(columns=tag_map)
    df[config.TIMESTAMP_COLUMN] = pd.to_datetime(df[config.TIMESTAMP_COLUMN])

    # Set index and sort before filtering
    df = df.set_index(config.TIMESTAMP_COLUMN).sort_index()

    # Apply configured signal filtering rules on RAW data BEFORE oversampling
    try:
        import process_model
        df = process_model.apply_signal_filters(df)
    except Exception as e:
        print(f"Error applying signal filters: {e}")

    # 5. Resample and Fill (Pandas 3.0 Syntax: No 'method' in fillna)
    df = df.resample(config.RESAMPLE_INTERVAL).first()

    if config.FILL_METHOD == 'bfill':
        df = df.bfill()
    else:
        df = df.ffill()

    df = df.reset_index()

    return df


def get_realtime_data_window(start_time, end_time, process_tags, tag_map):
    client = get_db_client()
    if not client: return pd.DataFrame()

    try:
        field_filters = ' or '.join([f'r["_field"] == "{tag}"' for tag in process_tags])
        query = f'''
        from(bucket: "{config.DB_BUCKET}")
          |> range(start: {start_time.isoformat()}Z, stop: {end_time.isoformat()}Z)
          |> filter(fn: (r) => r["_measurement"] == "{config.DB_MEASUREMENT_OPC}" or r["_measurement"] == "{config.DB_MEASUREMENT_PI}" or r["_measurement"] == "{config.DB_MEASUREMENT}")
          |> filter(fn: (r) => {field_filters})
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        df = client.query_api().query_data_frame(org=config.DB_ORG, query=query)
        if isinstance(df, list): df = pd.concat(df) if df else pd.DataFrame()
        return _rename_and_format_df(df, tag_map) if not df.empty else pd.DataFrame()
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()
    finally:
        client.close()


def write_setpoints(timestamp, setpoints_dict, setpoint_tag_map, scale_factors):
    client = get_db_client()
    if not client: return False
    write_api = client.write_api(write_options=SYNCHRONOUS)
    try:
        point = Point(config.DB_MEASUREMENT_SETPOINTS).time(timestamp)
        for name, value in setpoints_dict.items():
            tag = setpoint_tag_map.get(name)
            if tag:
                point.field(tag, float(value * scale_factors.get(name, 1)))
        write_api.write(bucket=config.DB_BUCKET, org=config.DB_ORG, record=point)
        return True
    except Exception as e:
        print(f"Error writing setpoints: {e}")
        return False
    finally:
        write_api.close()
        client.close()