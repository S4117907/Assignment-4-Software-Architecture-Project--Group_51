"""Message Broker topic names (kept identical to infrastructure/message_broker/topics.yaml)."""

FARM_EVENTS = "farm.events"                          # FarmRegistered, FarmUpdated
DEVICE_EVENTS = "device.events"                      # DeviceRegistered, DeviceDecommissioned
TELEMETRY_RECEIVED = "telemetry.received"            # validated, normalised readings
ALERT_RAISED = "alert.raised"                        # consumed by External Integration Service
IRRIGATION_COMMAND_STATUS = "irrigation.command-status"  # device acknowledgements
