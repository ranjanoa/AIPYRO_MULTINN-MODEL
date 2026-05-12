# Guide: Exporting Calculated Variables to InfluxDB & PLC

This guide details the structural configuration trick allowing you to export calculated formulas directly to your destination databases or hardware, without editing any Python codebase, and while completely protecting your Neural Network inputs from data leakage.

## Overview of the Interaction
The system automatically merges variables dynamically:
- **`process_model.py` / Data Collection**: Resolves database mappings using the `control_variables` JSON section.
- **`mbrl_manager.py` / AI Training Engine**: Automatically excludes calculated variables & any variables with a priority of `0` to prevent training pollution.
- **`main.py` / Write Queue**: Pushes all "Hardware" tags, then does a secondary override loop to inject "Calculated" formulas directly into the write queue (e.g. InfluxDB/OPC UA).

By combining these rules, you can configure a single "Bridge Block" to bind your variables securely.

---

## 🚀 The Implementation Method

To route a calculated variable to `kiln2` (InfluxDB) and/or your PLC without editing code, you must create a **Dummy Bridge Block** inside the `"control_variables"` section of `model_config.json`.

### 1. Match the Name Exactly
Copy the EXACT `"friendly_name"` of your calculated variable. 
For example: `"Kiln filling degree (%) SP"`.

### 2. Create the JSON Bridge Block
Insert the dummy variable inside the `"control_variables"` section like so:

```json
  "control_variables": {

    "Kiln filling degree (%) SP": {
      "is_setpoint": true,
      "tag_name": "your_db_column_name_here",
      "opc_tag": "ns=2;s=YOUR_REAL_PLC_NODE_ID",
      "scale_factor": 1.0,
      "priority": 0 
    },

    "Dividing gate position Cyclone 3": {
      "aipc": true,
      ...
```

### 3. Understanding the Flags:
- **`is_setpoint: true`** -> Flags the variable as eligible for database/hardware routing.
- **`tag_name: "..."`** -> The actual column name where the value gets written inside `kiln2` / InfluxDB.
- **`opc_tag: "..."`** -> *(Optional)* The address for your PLC. (Only needed if utilizing `control_service.py` to write directly to hardware).
- **`scale_factor: 1.0`** -> A multiplier applied to the target before saving it to InfluxDB.
- **`priority: 0`** -> **CRITICAL**. This forcefully instructs the Neural Network training suite (`mbrl_manager.py`) to completely ignore this variable and prevent it from becoming part of the state/action space during training.

---

## ⚠️ Important Note Regarding the PLC Scale Factor

If you intend to write to the PLC via `control_service.py` (and not just via a secondary script reading `kiln2`), you should be aware of a hardcoded limitation:

- **InfluxDB (`kiln2`)** correctly scales using `"scale_factor"` before writing.
- **PLC (`control_service.py`)** skips the math entirely and writes the raw value to the OPC node.

If you decide you need `control_service.py` to apply the `scale_factor` in the future, you will need to apply a two-line fix around line `170` of `control_service.py`:

**Change this:**
```python
node.set_value(ua.DataValue(ua.Variant(float(val), ua.VariantType.Float)))
```
**To this:**
```python
scale = var_conf.get('scale_factor', 1.0)
node.set_value(ua.DataValue(ua.Variant(float(val * scale), ua.VariantType.Float)))
```
