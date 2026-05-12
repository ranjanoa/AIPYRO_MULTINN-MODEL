# database.py - Updated for Pandas 3.0 & InfluxDB _time mapping
import config
import pandas as pd
import numpy as np
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

    # Set index, sort, and merge exact duplicate timestamps from multiple tables before filtering
    df = df.set_index(config.TIMESTAMP_COLUMN).sort_index()
    if df.index.duplicated().any():
        df = df.groupby(level=0).first()

    # Apply configured signal filtering rules on RAW data BEFORE oversampling
    try:
        import process_model
        df = process_model.apply_signal_filters(df)
    except Exception as e:
        print(f"Error applying signal filters: {e}")

    # 5. Resample and Fill:
    # Use mean() for numeric columns to preserve high-frequency signal fidelity without 'flattening',
    # and use first() for categorical/string columns (like 'Coal Mill (ON/OFF)') to prevent dropping them.
    resampled = df.resample(config.RESAMPLE_INTERVAL)
    numeric_df = resampled.mean(numeric_only=True)
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns
    
    if not non_numeric_cols.empty:
        non_numeric_df = resampled.first()[non_numeric_cols]
        df = pd.concat([numeric_df, non_numeric_df], axis=1)
    else:
        df = numeric_df

    if config.FILL_METHOD == 'bfill':
        df = df.bfill().ffill()
    else:
        df = df.ffill().bfill()

    # Sanitize subnormal floats from disconnected PLCs (e.g., 1e-39) to exactly 0.0
    # This prevents the UI from rendering weird scientific notation characters (like â‚¬<39â‚¬<-)
    # and prevents the AI from calculating infinite uncertainties.
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if not numeric_cols.empty:
        df[numeric_cols] = df[numeric_cols].apply(lambda x: np.where(np.abs(x) < 1e-10, 0.0, x))

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


def get_aimnm_results(window_minutes=2):
    """
    Reads the latest record from `cimpor_data_result` (DB_MEASUREMENT_AI_MNM_RESULT).
    Returns a flat dict {field_name: float_value, _time: ISO} — frontend pairs
    `<param>_curr` with `<param>_sp` to render Curr/SP columns.
    """
    client = get_db_client()
    if not client:
        return {}
    try:
        query = f'''
        from(bucket: "{config.DB_BUCKET}")
          |> range(start: -{int(window_minutes)}m)
          |> filter(fn: (r) => r["_measurement"] == "{config.DB_MEASUREMENT_AI_MNM_RESULT}")
          |> last()
          |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
        '''
        df = client.query_api().query_data_frame(org=config.DB_ORG, query=query)
        if isinstance(df, list):
            df = pd.concat(df) if df else pd.DataFrame()
        if df is None or df.empty:
            return {}

        cols_to_drop = [c for c in ['result', 'table', '_start', '_stop', '_measurement'] if c in df.columns]
        df = df.drop(columns=cols_to_drop)
        row = df.iloc[-1].to_dict()
        out = {}
        for k, v in row.items():
            if k == '_time':
                out['_time'] = str(v)
                continue
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                continue
        return out
    except Exception as e:
        print(f"get_aimnm_results error: {e}")
        return {}
    finally:
        client.close()


def get_kiln1_latest_fields(field_names, window_minutes=5):
    """
    Reads the latest values for the given field_names from the `kiln1`
    (DB_MEASUREMENT) measurement.

    AI_MNM uses this to populate the right-side Live Sensors panel. Field
    names are passed through verbatim (case-sensitive, including spaces and
    parentheses) because the AI engine writes them that way.

    Returns: { field_name: float_value, _time: ISO } — fields that don't
    exist on the latest point are simply omitted.
    """
    if not field_names:
        return {}
    client = get_db_client()
    if not client:
        return {}
    try:
        filter_clause = " or ".join(
            f'r["_field"] == "{str(fn).replace(chr(34), chr(92) + chr(34))}"'
            for fn in field_names
        )
        query = f'''
        from(bucket: "{config.DB_BUCKET}")
          |> range(start: -{int(window_minutes)}m)
          |> filter(fn: (r) => r["_measurement"] == "{config.DB_MEASUREMENT}")
          |> filter(fn: (r) => {filter_clause})
          |> last()
          |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
        '''
        df = client.query_api().query_data_frame(org=config.DB_ORG, query=query)
        if isinstance(df, list):
            df = pd.concat(df) if df else pd.DataFrame()
        if df is None or df.empty:
            return {}
        cols_to_drop = [c for c in ['result', 'table', '_start', '_stop', '_measurement'] if c in df.columns]
        df = df.drop(columns=cols_to_drop)
        row = df.iloc[-1].to_dict()
        out = {}
        for k, v in row.items():
            if k == '_time':
                out['_time'] = str(v)
                continue
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                continue
        return out
    except Exception as e:
        print(f"get_kiln1_latest_fields error: {e}")
        return {}
    finally:
        client.close()


def _aimnm_field_name(param):
    """
    Build the kiln2 field name for an AI_MNM CV SP.
    Flatten to `aimnm_<param>` with all underscores/spaces stripped, e.g.:
        kiln_feed             -> aimnm_kilnfeed
        main_firing_petcoke   -> aimnm_mainfiringpetcoke
    """
    flat = ''.join(ch for ch in str(param) if ch.isalnum())
    return f"aimnm_{flat.lower()}"


def mirror_aimnm_cv_to_kiln2(cv_pairs):
    """
    Mirrors AI_MNM CV setpoints into kiln2 (DB_MEASUREMENT_SETPOINTS) on every poll.
    ONLY the SP value is persisted to kiln2. Indicator values are NOT persisted.

    `cv_pairs` shape: { "<param>": {"curr": float|None, "sp": float|None} }
    """
    from datetime import datetime, timezone
    if not cv_pairs:
        return False
    client = get_db_client()
    if not client:
        return False
    write_api = client.write_api(write_options=SYNCHRONOUS)
    try:
        point = Point(config.DB_MEASUREMENT_SETPOINTS).time(datetime.now(timezone.utc))
        wrote_any = False
        for param, vals in cv_pairs.items():
            if not isinstance(vals, dict):
                continue
            v = vals.get('sp')
            if v is None:
                continue
            try:
                point.field(_aimnm_field_name(param), float(v))
                wrote_any = True
            except (TypeError, ValueError):
                continue
        if not wrote_any:
            return True
        write_api.write(bucket=config.DB_BUCKET, org=config.DB_ORG, record=point)
        return True
    except Exception as e:
        print(f"mirror_aimnm_cv_to_kiln2 error: {e}")
        return False
    finally:
        write_api.close()
        client.close()


def write_aimnm_setpoints(values_dict):
    """
    DEPRECATED — retained as a no-op for backward compatibility.
    AI_MNM setpoints are written via mirror_aimnm_cv_to_kiln2.
    Configuration lives in model_config.json only.
    """
    return True