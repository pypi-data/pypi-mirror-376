"""快递鸟API数据模型定义"""

from enum import IntEnum
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TrackingState(IntEnum):
    """物流状态"""
    NO_TRACE = 0
    COLLECTED = 1
    IN_TRANSIT = 2
    SIGNED = 3
    PROBLEM = 4
    FORWARDED = 5
    CUSTOMS = 6


class DetailedTrackingState(IntEnum):
    """详细物流状态定义"""
    # 基本状态
    NO_TRACE = 0
    COLLECTED = 1
    IN_TRANSIT = 2
    SIGNED = 3
    PROBLEM = 4
    FORWARDED = 5
    CUSTOMS = 6
    
    # 详细状态
    WAITING_PICKUP = 10
    ARRIVED_DESTINATION = 201
    OUT_FOR_DELIVERY = 202
    IN_LOCKER_STATION = 211
    AT_SORTING_CENTER = 204
    AT_DELIVERY_POINT = 205
    DISPATCHED_FROM_ORIGIN = 206
    NORMAL_DELIVERY = 301
    DELIVERED_AFTER_PROBLEM = 302
    PROXY_DELIVERY = 304
    LOCKER_DELIVERY = 311
    NO_SHIPPING_INFO = 401
    DELIVERY_TIMEOUT = 402
    UPDATE_TIMEOUT = 403
    REJECTED = 404
    DELIVERY_EXCEPTION = 405
    RETURN_DELIVERED = 406
    RETURN_NOT_DELIVERED = 407
    LOCKER_TIMEOUT = 412
    INTERCEPTED = 413
    DAMAGED = 414
    CANCELLED = 415
    UNREACHABLE = 416
    DELIVERY_DELAYED = 417
    REMOVED_FROM_LOCKER = 418
    REDELIVERY = 419
    ADDRESS_INCOMPLETE = 420
    PHONE_ERROR = 421
    MISSORTED = 422
    OUT_OF_RANGE = 423
    AWAITING_CLEARANCE = 601
    CLEARING_CUSTOMS = 602
    CUSTOMS_CLEARED = 603
    CUSTOMS_EXCEPTION = 604


class TrackTrace(BaseModel):
    """轨迹信息"""
    AcceptTime: str = Field(..., description="时间 '2024-01-15 10:30:00'")
    AcceptStation: str = Field(..., description="描述")
    Remark: Optional[str] = Field(None, description="备注")
    Location: Optional[str] = Field(None, description="所在城市")


class TrackRequest(BaseModel):
    """轨迹查询请求"""
    LogisticCode: str = Field(..., description="快递单号")
    ShipperCode: Optional[str] = Field(None, description="快递公司编码，如 'STO', 'YTO', 'ZTO'")
    CustomerName: Optional[str] = Field(None, description="手机号后四位（顺丰必填）")


class TrackResponse(BaseModel):
    """轨迹查询响应"""
    EBusinessID: str
    Success: bool
    Reason: Optional[str] = None
    State: int = Field(..., description="物流状态码")
    StateEx: int = Field(..., description="详细物流状态码")
    LogisticCode: str
    ShipperCode: str
    Traces: List[TrackTrace] = Field(default_factory=list)


class ShipperInfo(BaseModel):
    """快递公司信息"""
    ShipperCode: str = Field(..., description="快递公司编码")
    ShipperName: str = Field(..., description="快递公司名称")


class RecognizeRequest(BaseModel):
    """单号识别请求"""
    LogisticCode: str = Field(..., description="快递单号")


class RecognizeResponse(BaseModel):
    """单号识别响应"""
    EBusinessID: str
    Success: bool
    LogisticCode: str
    Reason: Optional[str] = None
    Shippers: List[ShipperInfo] = Field(default_factory=list)


class TimeEfficiencyRequest(BaseModel):
    """时效预估请求"""
    ShipperCode: str = Field(..., description="快递公司编码")
    LogisticCode: Optional[str] = Field(None, description="发货后必填")
    SendProvince: str = Field(..., description="寄件省份")
    SendCity: str = Field(..., description="寄件城市")
    SendArea: str = Field(..., description="寄件区县")
    SendAddress: Optional[str] = Field(None, description="寄件详细地址")
    ReceiveProvince: str = Field(..., description="收件省份")
    ReceiveCity: str = Field(..., description="收件城市")
    ReceiveArea: str = Field(..., description="收件区县")
    ReceiveAddress: Optional[str] = Field(None, description="收件详细地址")
    CatchTime: Optional[str] = Field(None, description="揽收时间")
    SenderPhone: Optional[str] = Field(None, description="寄件人手机后四位（顺丰必填）")
    ReceiverPhone: Optional[str] = Field(None, description="收件人手机后四位（顺丰必填）")
    Weight: Optional[float] = Field(None, description="重量(KG)")
    Volume: Optional[float] = Field(None, description="体积(cm³)")
    Quantity: Optional[int] = Field(1, description="件数")


class TimeEfficiencyResponse(BaseModel):
    """时效预估响应"""
    EBusinessID: str
    Success: bool
    Reason: Optional[str] = None
    LogisticCode: Optional[str] = None
    ShipperCode: str
    SendProvince: Optional[str] = Field(None, description="始发省")
    SendCity: Optional[str] = Field(None, description="始发市")
    SendArea: Optional[str] = Field(None, description="始发区县")
    SendAddress: Optional[str] = Field(None, description="始发详细地址")
    ReceiveProvince: Optional[str] = Field(None, description="目的省")
    ReceiveCity: Optional[str] = Field(None, description="目的市")
    ReceiveArea: Optional[str] = Field(None, description="目的区县")
    ReceiveAddress: Optional[str] = Field(None, description="目的详细地址")
    LatestStation: Optional[str] = Field(None, description="最新轨迹发生的站点（发货后）")
    LatestProvince: Optional[str] = Field(None, description="最新所在省份（发货后）")
    LatestCity: Optional[str] = Field(None, description="最新所在城市（发货后）")
    LatestArea: Optional[str] = Field(None, description="最新所在区县（发货后）")
    DeliveryTime: Optional[str] = Field(None, description="预计送达时间，如：06月15日下午可达")
    DeliveryDate: Optional[str] = Field(None, description="预计送达日期，格式：2024-04-20")
    Hour: Optional[str] = Field(None, description="预计时效，如：36h")
    PredictPath: Optional[str] = Field(None, description="预估行驶线路")
    DeliveryMemo: Optional[str] = Field(None, description="备注（发货后）")


class AddressParseRequest(BaseModel):
    """地址解析请求"""
    Content: str = Field(..., description="待识别的完整地址，为提高准确率不同信息可用空格区分")


class AddressParseData(BaseModel):
    """地址解析数据"""
    Name: Optional[str] = Field(None, description="姓名")
    Mobile: Optional[str] = Field(None, description="手机号/座机号")
    ExtMobile: Optional[str] = Field(None, description="分机号")
    ProvinceName: Optional[str] = Field(None, description="省份")
    CityName: Optional[str] = Field(None, description="城市")
    ExpAreaName: Optional[str] = Field(None, description="所在地区/县级市")
    StreetName: Optional[str] = Field(None, description="街道名称")
    Address: Optional[str] = Field(None, description="详细地址")


class AddressParseResponse(BaseModel):
    """地址解析响应"""
    EBusinessID: str
    Success: bool
    Reason: Optional[str] = None
    ResultCode: str
    Data: Optional[AddressParseData] = None


# 快递公司编码映射
# 注意：详细的快递公司编码映射已移至kdniao_docs.py
from models.kdniao_docs import SHIPPER_CODES


def get_shipper_name(code: str) -> str:
    """根据编码获取快递公司名称
    
    注意：此函数使用kdniao_docs.py中的SHIPPER_CODES
    """
    from models.kdniao_docs import SHIPPER_CODES
    return SHIPPER_CODES.get(code.upper(), code)


def get_state_description(state: int, state_ex: int = None) -> str:
    """获取状态描述
    
    注意：此函数仅返回基本状态描述，详细状态描述请参考文档模型
    """
    # 从文档模型中获取状态描述
    from models.kdniao_docs import get_state_description as get_doc_state_description
    
    # 如果有详细状态，优先使用详细状态
    if state_ex is not None:
        return get_doc_state_description(state_ex=state_ex)
    
    return get_doc_state_description(state=state)