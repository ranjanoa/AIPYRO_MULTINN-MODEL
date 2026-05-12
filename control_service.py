import config
import logging
import time

try:
    from opcua import Client, ua
except ImportError:
    print("Warning: 'opcua' library not found. Install with: pip install opcua")
    Client = None
    ua = None

logger = logging.getLogger(__name__)


class ControlService:
    def __init__(self):
        self.client = None
        self.connected = False
        # Use localhost for local simulation, or config IP for real PLC
        self.url = getattr(config, 'OPC_URL', "opc.tcp://localhost:53530/OPCUA/SimulationServer")
        self.enabled = False  # <--- Default to Safe/Off
        self.last_connection_attempt = 0
        self.retry_delay = 5  # Seconds to wait before retrying a failed connection

    def connect(self):
        """
        Ensures a single persistent connection to the PLC.
        Prevents 'Too Many Sessions' errors by reusing the existing client.
        """
        if not Client: return False

        # Short-circuit: if PLC is not required, don't even attempt a connection
        if not getattr(config, 'REQUIRE_PLC', True):
            return False

        # Rate Limit: Don't spam the server if it's down (wait 5s or 10s)
        if not self.connected and (time.time() - self.last_connection_attempt < self.retry_delay):
            return False

        try:
            # 1. Test existing connection (Lightweight check)
            if self.connected and self.client:
                try:
                    # Read server status or time to verify connection is alive
                    self.client.get_node(ua.NodeId(ua.ObjectIds.Server_ServerStatus_CurrentTime)).get_value()
                    return True
                except:
                    logger.warning("Connection lost. Reconnecting...")
                    self.connected = False
                    try:
                        self.client.disconnect()
                    except:
                        pass

            # 2. Establish new connection
            self.last_connection_attempt = time.time()
            self.client = Client(self.url)
            self.client.connect()
            self.connected = True
            logger.info(f"Control Service Connected: {self.url}")
            return True

        except Exception as e:
            # Smart Error Logging
            if "BadTooManySessions" in str(e):
                logger.error("PLC Server Full. Pausing for 10s. (Please restart PLC Simulator)")
                self.retry_delay = 10
            else:
                if getattr(config, 'REQUIRE_PLC', True):
                    logger.error(f"PLC Connection Failed: {e}")
                self.retry_delay = 5

            self.connected = False
            return False

    def disconnect(self):
        """Closes connection cleanly."""
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
        self.connected = False

    # --- NEW METHOD ADDED HERE ---
    def set_enabled(self, active):
        """Enables or disables the writing logic based on UI Button."""
        self.enabled = active
        status = "ENABLED" if active else "DISABLED"
        logger.info(f"PLC Write Permission Set To: {status}")

    # -----------------------------

    def send_handshake(self, watchdog_counter, current_mode_int):
        """
        Writes Heartbeat & Status to the PLC.
        """
        if not getattr(config, 'REQUIRE_PLC', True):
            return  # PLC not required; skip handshake entirely
        if not self.connect(): return

        try:
            import process_model
            conf = process_model.load_model_config()
            hs = conf.get('opc_handshake', {})

            # 1. Write Watchdog (Heartbeat)
            if hs.get('watchdog_write'):
                node = self.client.get_node(hs['watchdog_write'])
                # Cast to float for Simulator compatibility
                val = ua.DataValue(ua.Variant(float(watchdog_counter), ua.VariantType.Float))
                node.set_value(val)

            # 2. Write Control Status (0=Monitor, 1=AI, 2=Fingerprint)
            if hs.get('status_write'):
                status_to_write = 3 if getattr(config, 'TEST_MODE', False) else current_mode_int
                node = self.client.get_node(hs['status_write'])
                # Cast to float for Simulator compatibility
                val = ua.DataValue(ua.Variant(float(status_to_write), ua.VariantType.Float))
                node.set_value(val)

        except Exception as e:
            logger.error(f"Handshake Error: {e}")
            # Force a reconnect on the next cycle if writing fails
            self.connected = False

    def execute_recommendation(self, recommendation_data):
        """
        Writes setpoints to the PLC, but ONLY if Autopilot is enabled.
        """
        # The Gatekeeper
        if not self.enabled:
            return False

        return self.write_immediate(recommendation_data.get('actions', []))

    def write_immediate(self, actions):
        """
        Writes setpoints IMMEDIATELY (Bypasses 'enabled' check).
        Used for Manual Batch Selection from UI.
        """
        if not actions: return True
        
        connected = self.connect()
        if not connected:
            if getattr(config, 'REQUIRE_PLC', True):
                return False
            else:
                logger.info(f"PLC not connected (REQUIRE_PLC=False). Skipping OPC write but simulating success for {len(actions)} setpoints.")
                return True

        try:
            import process_model
            conf = process_model.load_model_config()
            control_vars = conf.get('control_variables', {})

            for action in actions:
                var_name = action.get('var_name')

                # Logic to find the value (Handles both AI and Fingerprint keys)
                val = action.get('fingerprint_set_point')
                if val is None:
                    val = action.get('setpoint')  # Fallback key

                # Get the OPC Node ID from config
                var_conf = control_vars.get(var_name, {})
                opc_tag = var_conf.get('opc_tag')

                if opc_tag and val is not None:
                    node = self.client.get_node(opc_tag)
                    # Setpoints are Float/Double
                    node.set_value(ua.DataValue(ua.Variant(float(val), ua.VariantType.Float)))

            logger.info(f"PLC WRITE: Sent {len(actions)} setpoints.")
            return True

        except Exception as e:
            logger.error(f"Write Setpoints Error: {e}")
            self.connected = False
            return False


# Singleton Instance
service = ControlService()