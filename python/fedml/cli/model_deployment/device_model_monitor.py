import argparse
import json
import time
import uuid

from fedml.cli.model_deployment.device_model_cache import FedMLModelCache
from fedml.cli.model_deployment.modelops_configs import ModelOpsConfigs
from fedml.core.distributed.communication.mqtt.mqtt_manager import MqttManager


class FedMLModelMetrics:
    def __init__(self, end_point_id, model_id, model_name, infer_url):
        self.current_end_point_id = end_point_id
        self.current_model_id = model_id,
        self.current_model_name = model_name
        self.current_infer_url = infer_url
        self.start_time = time.time_ns()
        self.monitor_mqtt_mgr = None
        self.config_version = "dev"
        self.ms_per_sec = 1000
        self.ns_per_ms = 1000 * 1000

    def set_start_time(self):
        self.start_time = time.time_ns()

    def calc_metrics(self, model_id, model_name, end_point_id, inference_output_url):
        total_latency, avg_latency, total_request_num, current_qps, timestamp = 0, 0, 0, 0, 0
        metrics_item = FedMLModelCache.get_instance().get_latest_monitor_metrics(end_point_id)
        if metrics_item is not None:
            total_latency, avg_latency, total_request_num, current_qps, timestamp = \
                FedMLModelCache.get_instance().get_metrics_item_info(metrics_item)
        cost_time = (time.time_ns() - self.start_time) / self.ns_per_ms
        total_latency += cost_time
        total_request_num += 1
        current_qps = 1 / (cost_time / self.ms_per_sec)
        current_qps = format(current_qps, '.0f')
        avg_latency = format(total_latency / total_request_num / self.ms_per_sec, '.6f')

        FedMLModelCache.get_instance().set_monitor_metrics(end_point_id, total_latency, avg_latency,
                                                           total_request_num, current_qps,
                                                           int(format(time.time(), '.0f')))

    def start_monitoring_metrics_center(self):
        self.build_metrics_report_channel()

    def build_metrics_report_channel(self):
        args = {"config_version": "release"}
        mqtt_config, _ = ModelOpsConfigs.get_instance(args).fetch_configs(self.config_version)
        self.monitor_mqtt_mgr = MqttManager(
            mqtt_config["BROKER_HOST"],
            mqtt_config["BROKER_PORT"],
            mqtt_config["MQTT_USER"],
            mqtt_config["MQTT_PWD"],
            mqtt_config["MQTT_KEEPALIVE"],
            "FedML_ModelMonitor_" + str(uuid.uuid4())
        )
        self.monitor_mqtt_mgr.add_connected_listener(self.on_mqtt_connected)
        self.monitor_mqtt_mgr.add_disconnected_listener(self.on_mqtt_disconnected)
        self.monitor_mqtt_mgr.connect()
        self.monitor_mqtt_mgr.loop_start()

        index = 0
        while True:
            time.sleep(2)
            index = self.send_monitoring_metrics(index)

        self.monitor_mqtt_mgr.disconnect()
        self.monitor_mqtt_mgr.loop_stop()

    def send_monitoring_metrics(self, index):
        metrics_item, inc_index = FedMLModelCache.get_instance().get_monitor_metrics_item(self.current_end_point_id,
                                                                                          index)
        if metrics_item is None:
            return index
        total_latency, avg_latency, total_request_num, current_qps, timestamp = \
            FedMLModelCache.get_instance().get_metrics_item_info(metrics_item)
        deployment_monitoring_topic = "/model_ops/model_device/return_inference_monitoring/{}".format(
            self.current_end_point_id)
        deployment_monitoring_payload = {"model_name": self.current_model_name,
                                         "model_id": self.current_model_id,
                                         "model_url": self.current_infer_url,
                                         "end_point_id": self.current_end_point_id,
                                         "latency": float(avg_latency),
                                         "qps": int(current_qps),
                                         "total_request_num": int(total_request_num),
                                         "timestamp": timestamp}

        self.monitor_mqtt_mgr.send_message_json(deployment_monitoring_topic,
                                                json.dumps(deployment_monitoring_payload))
        return inc_index

    def on_mqtt_connected(self, mqtt_client_object):
        pass

    def on_mqtt_disconnected(self, mqtt_client_object):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--end_point_id", "-ep", help="end point id")
    parser.add_argument("--model_id", "-mi", type=str, help='model id')
    parser.add_argument("--model_name", "-mn", type=str, help="model name")
    parser.add_argument("--infer_url", "-iu", type=str, help="inference url")
    args = parser.parse_args()

    monitor_center = FedMLModelMetrics(args.end_point_id, args.model_id, args.model_name, args.infer_url)
    monitor_center.start_monitoring_metrics_center()

