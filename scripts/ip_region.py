"""
IP 地域查询工具 (基于 ip2region.xdb)
使用离线数据文件，无需网络请求
"""

import os
import struct
import socket

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
XDB_PATH = os.path.join(_SCRIPT_DIR, "ip2region_v4.xdb")

HEADER_INFO_SIZE = 256
VECTOR_INDEX_SIZE = 256 * 256 * 8  # 512 KiB vector index
SEGMENT_INDEX_SIZE = 14  # start_ip(4) + end_ip(4) + data_length(2) + data_ptr(4)


def _ip_to_int(ip: str) -> int:
    """IP地址转32位整数"""
    return struct.unpack("!I", socket.inet_aton(ip))[0]


class IpRegionSearcher:
    def __init__(self, xdb_path: str = None):
        self._path = xdb_path or XDB_PATH
        self._fd = None

    def open(self):
        if not os.path.exists(self._path):
            raise FileNotFoundError(f"xdb file not found at: {self._path}")
        self._fd = open(self._path, "rb")

    def close(self):
        if self._fd:
            self._fd.close()
            self._fd = None

    def search(self, ip: str) -> str:
        """根据IP查询地域信息，返回 "国家|区域|省份|城市|ISP" 格式"""
        if self._fd is None:
            self.open()
        try:
            ip_int = _ip_to_int(ip)
        except (OSError, struct.error):
            return ""

        self._fd.seek(0)
        header = self._fd.read(HEADER_INFO_SIZE)
        if len(header) < 16:
            return ""

        # v3 header: version(2) + cache_policy(2) + created_at(4) + start_ptr(4) + end_ptr(4) + ...
        version = struct.unpack("<H", header[0:2])[0]
        start_index_ptr = struct.unpack("<I", header[8:12])[0]
        end_index_ptr = struct.unpack("<I", header[12:16])[0]

        # 二分索引段的总段数
        total_segments = (end_index_ptr - start_index_ptr) // SEGMENT_INDEX_SIZE
        if total_segments == 0:
            return ""

        left = 0
        right = total_segments - 1

        data_ptr = 0
        data_length = 0

        while left <= right:
            mid = (left + right) // 2
            self._fd.seek(start_index_ptr + mid * SEGMENT_INDEX_SIZE)
            segment = self._fd.read(SEGMENT_INDEX_SIZE)
            if len(segment) < SEGMENT_INDEX_SIZE:
                break

            start_ip = struct.unpack("<I", segment[0:4])[0]
            end_ip = struct.unpack("<I", segment[4:8])[0]

            if ip_int < start_ip:
                right = mid - 1
            elif ip_int > end_ip:
                left = mid + 1
            else:
                data_length = struct.unpack("<H", segment[8:10])[0]
                data_ptr = struct.unpack("<I", segment[10:14])[0]
                break

        if data_ptr == 0 or data_length == 0:
            return ""

        self._fd.seek(data_ptr)
        region_data = self._fd.read(data_length)
        return region_data.decode("utf-8", errors="ignore")


# 全局单例
_searcher = None


def get_province(ip: str) -> str:
    """
    根据IP获取省份/州
    返回: 省份名 (如 "广东省", "Queensland") 或 "未知"
    """
    global _searcher
    if _searcher is None:
        _searcher = IpRegionSearcher()
        try:
            _searcher.open()
        except FileNotFoundError:
            return "未知"

    try:
        result = _searcher.search(ip)
        if not result:
            return "其他"
        # ip2region 格式: "国家|省份|城市|0|国家代码" 或 "国家|0|省份|城市|ISP"
        parts = result.split("|")
        # 取第一个像省份的字段：非空且不是纯数字，跳过国家名
        for i in range(1, len(parts)):
            val = parts[i].strip()
            if val and val != "0" and not val.isdigit():
                return val
        return "其他"
    except Exception:
        return "未知"
