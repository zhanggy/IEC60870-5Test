"""
数据点管理器
负责管理和存储所有数据点的值
"""

import threading
from typing import Dict, Any, Optional


class DataPoint:
    """数据点基类"""

    def __init__(self, ioa: int, value: Any, quality: int = 0):
        self.ioa = ioa
        self.value = value
        self.quality = quality
        self.lock = threading.Lock()

    def get_value(self):
        """获取值"""
        with self.lock:
            return self.value, self.quality

    def set_value(self, value: Any, quality: int = 0):
        """设置值"""
        with self.lock:
            self.value = value
            self.quality = quality


class DataPointManager:
    """数据点管理器"""

    def __init__(self):
        self.single_points: Dict[int, DataPoint] = {}      # 单点信息
        self.double_points: Dict[int, DataPoint] = {}      # 双点信息
        self.step_positions: Dict[int, DataPoint] = {}     # 步位置信息
        self.normalized_values: Dict[int, DataPoint] = {}  # 归一化测量值
        self.scaled_values: Dict[int, DataPoint] = {}      # 标度化测量值
        self.float_values: Dict[int, DataPoint] = {}       # 短浮点测量值
        self.lock = threading.Lock()

    def add_single_point(self, ioa: int, value: bool, quality: int = 0):
        """添加单点信息"""
        with self.lock:
            self.single_points[ioa] = DataPoint(ioa, value, quality)

    def add_double_point(self, ioa: int, value: int, quality: int = 0):
        """添加双点信息"""
        with self.lock:
            self.double_points[ioa] = DataPoint(ioa, value, quality)

    def add_step_position(self, ioa: int, value: int, quality: int = 0):
        """添加步位置信息"""
        with self.lock:
            self.step_positions[ioa] = DataPoint(ioa, value, quality)

    def add_normalized_value(self, ioa: int, value: float, quality: int = 0):
        """添加归一化测量值"""
        with self.lock:
            self.normalized_values[ioa] = DataPoint(ioa, value, quality)

    def add_scaled_value(self, ioa: int, value: int, quality: int = 0):
        """添加标度化测量值"""
        with self.lock:
            self.scaled_values[ioa] = DataPoint(ioa, value, quality)

    def add_float_value(self, ioa: int, value: float, quality: int = 0):
        """添加短浮点测量值"""
        with self.lock:
            self.float_values[ioa] = DataPoint(ioa, value, quality)

    def get_single_point(self, ioa: int) -> Optional[tuple]:
        """获取单点信息"""
        with self.lock:
            if ioa in self.single_points:
                return self.single_points[ioa].get_value()
        return None

    def get_double_point(self, ioa: int) -> Optional[tuple]:
        """获取双点信息"""
        with self.lock:
            if ioa in self.double_points:
                return self.double_points[ioa].get_value()
        return None

    def get_step_position(self, ioa: int) -> Optional[tuple]:
        """获取步位置信息"""
        with self.lock:
            if ioa in self.step_positions:
                return self.step_positions[ioa].get_value()
        return None

    def get_normalized_value(self, ioa: int) -> Optional[tuple]:
        """获取归一化测量值"""
        with self.lock:
            if ioa in self.normalized_values:
                return self.normalized_values[ioa].get_value()
        return None

    def get_scaled_value(self, ioa: int) -> Optional[tuple]:
        """获取标度化测量值"""
        with self.lock:
            if ioa in self.scaled_values:
                return self.scaled_values[ioa].get_value()
        return None

    def get_float_value(self, ioa: int) -> Optional[tuple]:
        """获取短浮点测量值"""
        with self.lock:
            if ioa in self.float_values:
                return self.float_values[ioa].get_value()
        return None

    def set_single_point(self, ioa: int, value: bool, quality: int = 0) -> bool:
        """设置单点信息"""
        with self.lock:
            if ioa in self.single_points:
                self.single_points[ioa].set_value(value, quality)
                return True
        return False

    def set_double_point(self, ioa: int, value: int, quality: int = 0) -> bool:
        """设置双点信息"""
        with self.lock:
            if ioa in self.double_points:
                self.double_points[ioa].set_value(value, quality)
                return True
        return False

    def get_all_single_points(self) -> Dict[int, tuple]:
        """获取所有单点信息"""
        with self.lock:
            return {ioa: dp.get_value() for ioa, dp in self.single_points.items()}

    def get_all_double_points(self) -> Dict[int, tuple]:
        """获取所有双点信息"""
        with self.lock:
            return {ioa: dp.get_value() for ioa, dp in self.double_points.items()}

    def get_all_step_positions(self) -> Dict[int, tuple]:
        """获取所有步位置信息"""
        with self.lock:
            return {ioa: dp.get_value() for ioa, dp in self.step_positions.items()}

    def get_all_normalized_values(self) -> Dict[int, tuple]:
        """获取所有归一化测量值"""
        with self.lock:
            return {ioa: dp.get_value() for ioa, dp in self.normalized_values.items()}

    def get_all_scaled_values(self) -> Dict[int, tuple]:
        """获取所有标度化测量值"""
        with self.lock:
            return {ioa: dp.get_value() for ioa, dp in self.scaled_values.items()}

    def get_all_float_values(self) -> Dict[int, tuple]:
        """获取所有短浮点测量值"""
        with self.lock:
            return {ioa: dp.get_value() for ioa, dp in self.float_values.items()}

    def load_from_config(self, config: dict):
        """从配置加载数据点"""
        data_points = config.get('data_points', {})

        # 加载单点信息
        for sp in data_points.get('single_point', []):
            self.add_single_point(sp['ioa'], sp['value'], sp.get('quality', 0))

        # 加载双点信息
        for dp in data_points.get('double_point', []):
            self.add_double_point(dp['ioa'], dp['value'], dp.get('quality', 0))

        # 加载步位置信息
        for stp in data_points.get('step_position', []):
            self.add_step_position(stp['ioa'], stp['value'], stp.get('quality', 0))

        # 加载归一化测量值
        for nv in data_points.get('measured_normalized', []):
            self.add_normalized_value(nv['ioa'], nv['value'], nv.get('quality', 0))

        # 加载标度化测量值
        for sv in data_points.get('measured_scaled', []):
            self.add_scaled_value(sv['ioa'], sv['value'], sv.get('quality', 0))

        # 加载短浮点测量值
        for fv in data_points.get('measured_float', []):
            self.add_float_value(fv['ioa'], fv['value'], fv.get('quality', 0))
