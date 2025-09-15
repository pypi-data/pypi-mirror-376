# listener_bindings.pyi
from typing import Optional, Any, TypeVar, Generic
from .types import (

)

T = TypeVar('T')
TSeq = TypeVar('TSeq')
TDataReader = TypeVar('TDataReader')
# DDS_All.pyi
from typing import Optional, Any, List, Union
from .types import (

)

# -------------------------- 基本类型定义 --------------------------
def register_all_types(participant: DomainParticipant) -> None:
    """
    向给定的域参与者注册所有已知的 DDS 类型。

    :param participant: 域参与者实例。
    """

class StatusCondition:
    """状态条件类"""
    pass

class StatusKindMask:
    """状态类型掩码"""
    def __init__(self) -> None: ...

class InstanceHandle_t:
    """实例句柄"""
    valid: bool
    value: List[int]

    def __init__(self) -> None: ...

class DataReaderQos:
    """数据读取器QoS配置"""
    reliability: ReliabilityQosPolicy
    history: HistoryQosPolicy

    def __init__(self) -> None: ...

class SubscriptionMatchedStatus:
    """订阅匹配状态"""
    total_count: int
    total_count_change: int
    current_count: int
    current_count_change: int
    last_publication_handle: InstanceHandle_t

    def __init__(self) -> None: ...

class SubscriberQos:
    """订阅者QoS配置"""
    def __init__(self) -> None: ...

class DomainParticipantQos:
    """域参与者QoS配置"""
    def __init__(self) -> None: ...

class DomainParticipantFactoryQos:
    """域参与者工厂QoS配置"""
    def __init__(self) -> None: ...

class DataWriterQos:
    """数据写入器QoS配置"""
    reliability: ReliabilityQosPolicy
    history: HistoryQosPolicy

    def __init__(self) -> None: ...

class PublisherQos:
    """发布者QoS配置"""
    def __init__(self) -> None: ...

class TopicQos:
    """主题QoS配置"""
    def __init__(self) -> None: ...

class ReliabilityQosPolicy:
    """可靠性QoS策略"""
    kind: ReliabilityQosPolicyKind
    max_blocking_time: Any  # Duration_t类型

    def __init__(self) -> None: ...

class HistoryQosPolicy:
    """历史QoS策略"""
    kind: HistoryQosPolicyKind
    depth: int

    def __init__(self) -> None: ...

class PublicationMatchedStatus:
    """发布匹配状态"""
    total_count: int
    total_count_change: int
    current_count: int
    current_count_change: int
    last_subscription_handle: InstanceHandle_t

    def __init__(self) -> None: ...

# -------------------------- 枚举类型 --------------------------

class ReliabilityQosPolicyKind:
    """可靠性QoS策略类型枚举"""
    BEST_EFFORT_RELIABILITY_QOS: int
    RELIABLE_RELIABILITY_QOS: int

class HistoryQosPolicyKind:
    """历史QoS策略类型枚举"""
    KEEP_LAST_HISTORY_QOS: int
    KEEP_ALL_HISTORY_QOS: int

class StatusKind:
    """状态类型枚举"""
    INCONSISTENT_TOPIC_STATUS: int
    OFFERED_DEADLINE_MISSED_STATUS: int
    REQUESTED_DEADLINE_MISSED_STATUS: int
    OFFERED_INCOMPATIBLE_QOS_STATUS: int
    REQUESTED_INCOMPATIBLE_QOS_STATUS: int
    SAMPLE_LOST_STATUS: int
    SAMPLE_REJECTED_STATUS: int
    DATA_ON_READERS_STATUS: int
    DATA_AVAILABLE_STATUS: int
    LIVELINESS_LOST_STATUS: int
    LIVELINESS_CHANGED_STATUS: int
    PUBLICATION_MATCHED_STATUS: int
    SUBSCRIPTION_MATCHED_STATUS: int

# -------------------------- 实体类 --------------------------

class Entity:
    """DDS实体基类"""

    def get_statuscondition(self) -> StatusCondition:
        """获取状态条件"""
        ...

    def get_status_changes(self) -> StatusKindMask:
        """获取状态变化"""
        ...

    def enable(self) -> ReturnCode_t:
        """启用实体"""
        ...

    def get_instance_handle(self) -> InstanceHandle_t:
        """获取实例句柄"""
        ...

class Topic(Entity):
    """DDS主题"""
    pass

class DataReader(Entity):
    """数据读取器"""

    def enable(self) -> ReturnCode_t:
        """启用数据读取器"""
        ...

    def set_listener(self, listener: Optional[DataReaderListener] = None, mask: int = 0) -> ReturnCode_t:
        """
        设置监听器

        :param listener: 监听器实例
        :param mask: 状态掩码
        :return: 返回码
        """
        ...

    def get_subscription_matched_status(self) -> SubscriptionMatchedStatus:
        """
        获取订阅匹配状态

        :return: 订阅匹配状态
        :raises RuntimeError: 获取失败时抛出
        """
        ...

class DataWriter(Entity):
    """数据写入器"""

    def get_publication_matched_status(self) -> PublicationMatchedStatus:
        """
        获取发布匹配状态

        :return: 发布匹配状态
        :raises RuntimeError: 获取失败时抛出
        """
        ...

class Publisher(Entity):
    """发布者"""

    def create_datawriter(self, the_topic: Topic, qoslist: Union[DataWriterQos, int, None] = None,
                         a_listener: Optional[DataWriterListener] = None, mask: int = 0) -> DataWriter:
        """
        创建数据写入器

        :param the_topic: 目标主题
        :param qoslist: QoS配置，None或-1表示使用默认
        :param a_listener: 监听器
        :param mask: 状态掩码
        :return: 数据写入器实例
        """
        ...

    def get_default_datawriter_qos(self, qoslist: DataWriterQos) -> ReturnCode_t:
        """
        获取默认数据写入器QoS

        :param qoslist: 输出参数，存储获取的QoS
        :return: 返回码
        :raises RuntimeError: 获取失败时抛出
        """
        ...

class Subscriber(Entity):
    """订阅者"""

    def create_datareader(self, a_topic: Topic, qoslist: Union[DataReaderQos, int, None] = None,
                         a_listener: Optional[DataReaderListener] = None, mask: int = 0) -> DataReader:
        """
        创建数据读取器

        :param a_topic: 目标主题
        :param qoslist: QoS配置，None或-1表示使用默认
        :param a_listener: 监听器
        :param mask: 状态掩码
        :return: 数据读取器实例
        """
        ...

    def get_default_datareader_qos(self, qoslist: DataReaderQos) -> ReturnCode_t:
        """
        获取默认数据读取器QoS

        :param qoslist: 输出参数，存储获取的QoS
        :return: 返回码
        :raises RuntimeError: 获取失败时抛出
        """
        ...

class DomainParticipant(Entity):
    """域参与者"""

    def create_subscriber(self, qos: Union[SubscriberQos, int, None] = None,
                         listener: Optional[SubscriberListener] = None, mask: int = 0) -> Subscriber:
        """
        创建订阅者

        :param qos: QoS配置，None或-1表示使用默认
        :param listener: 监听器
        :param mask: 状态掩码
        :return: 订阅者实例
        """
        ...

    def create_publisher(self, qoslist: Union[PublisherQos, int, None] = None,
                        a_listener: Optional[PublisherListener] = None, mask: int = 0) -> Publisher:
        """
        创建发布者

        :param qoslist: QoS配置，None或-1表示使用默认
        :param a_listener: 监听器
        :param mask: 状态掩码
        :return: 发布者实例
        """
        ...

    def create_topic(self, topic_name: str, type_name: str,
                    qoslist: Union[TopicQos, int, None] = None,
                    a_listener: Optional[TopicListener] = None, mask: int = 0) -> Topic:
        """
        创建主题

        :param topic_name: 主题名称
        :param type_name: 类型名称
        :param qoslist: QoS配置，None或-1表示使用默认
        :param a_listener: 监听器
        :param mask: 状态掩码
        :return: 主题实例
        """
        ...

    def delete_topic(self, a_topic: Topic) -> ReturnCode_t:
        """
        删除主题

        :param a_topic: 要删除的主题
        :return: 返回码
        """
        ...

    def delete_contained_entities(self) -> ReturnCode_t:
        """
        删除所有包含的实体

        :return: 返回码
        :raises RuntimeError: 删除失败时抛出
        """
        ...

class DomainParticipantFactory:
    """域参与者工厂（单例模式）"""

    @staticmethod
    def get_instance() -> 'DomainParticipantFactory':
        """
        获取域参与者工厂单例对象

        :return: 域参与者工厂实例
        """
        ...

    @staticmethod
    def get_instance_w_qos(qoslist: DomainParticipantFactoryQos) -> 'DomainParticipantFactory':
        """
        使用指定的QoS获取域参与者工厂单例对象

        :param qoslist: 工厂QoS配置
        :return: 域参与者工厂实例
        """
        ...

    def create_participant(self, domainId: int, qos: Union[DomainParticipantQos, int, None] = None,
                          listener: Optional[DomainParticipantListener] = None, mask: int = 0) -> DomainParticipant:
        """
        创建域参与者

        :param domainId: 域ID
        :param qos: QoS配置，None或-1表示使用默认
        :param listener: 监听器
        :param mask: 状态掩码
        :return: 域参与者实例
        """
        ...

    def delete_participant(self, a_dp: DomainParticipant) -> ReturnCode_t:
        """
        删除域参与者

        :param a_dp: 要删除的域参与者
        :return: 返回码
        """
        ...

    def get_default_participant_qos(self, qoslist: DomainParticipantQos) -> ReturnCode_t:
        """
        获取默认域参与者QoS配置

        :param qoslist: 输出参数，存储获取的QoS
        :return: 返回码
        """
        ...

    def get_qos(self, qoslist: DomainParticipantFactoryQos) -> ReturnCode_t:
        """
        获取域参与者工厂QoS配置

        :param qoslist: 输出参数，存储获取的QoS
        :return: 返回码
        """
        ...

# -------------------------- 常量定义 --------------------------

DOMAINPARTICIPANT_QOS_DEFAULT: int = -1
"""默认域参与者QoS"""

DOMAINPARTICIPANT_FACTORY_QOS_DEFAULT: int = -1
"""默认域参与者工厂QoS"""

PUBLISHER_QOS_DEFAULT: int = -1
"""默认发布者QoS"""

SUBSCRIBER_QOS_DEFAULT: int = -1
"""默认订阅者QoS"""

DATAWRITER_QOS_DEFAULT: int = -1
"""默认数据写入器QoS"""

DATAREADER_QOS_DEFAULT: int = -1
"""默认数据读取器QoS"""

TOPIC_QOS_DEFAULT: int = -1
"""默认主题QoS"""

DATAWRITER_QOS_USE_TOPIC_QOS: int = -2
"""使用主题QoS的数据写入器QoS"""

DATAREADER_QOS_USE_TOPIC_QOS: int = -2
"""使用主题QoS的数据读取器QoS"""




class Listener:
    """
    DDS 监听器基类。

    所有 DDS 监听器的抽象基类，提供基础监听功能。
    """

    def __init__(self) -> None:
        """初始化监听器。"""

    def __repr__(self) -> str:
        """返回监听器的字符串表示。"""


class DataReaderListener(Listener):
    """
    数据读取器监听器。

    处理数据读取器相关事件的监听器。
    """

    def __init__(self) -> None:
        """初始化数据读取器监听器。"""

    def on_data_available(self, reader: DataReader) -> None:
        """
        当有新数据可用时调用。

        :param reader: 触发事件的数据读取器。
        """

    def on_data_arrived(self, reader: DataReader, sample: Any, info: SampleInfo) -> None:
        """
        当数据到达时调用。

        :param reader: 触发事件的数据读取器。
        :param sample: 到达的数据样本。
        :param info: 样本信息。
        """

    def on_requested_deadline_missed(self, reader: DataReader, status: RequestedDeadlineMissedStatus) -> None:
        """
        当请求的截止期限错过时调用。

        :param reader: 触发事件的数据读取器。
        :param status: 截止期限错过状态。
        """

    def on_liveliness_changed(self, reader: DataReader, status: LivelinessChangedStatus) -> None:
        """
        当活跃性改变时调用。

        :param reader: 触发事件的数据读取器。
        :param status: 活跃性改变状态。
        """

    def on_sample_rejected(self, reader: DataReader, status: SampleRejectedStatus) -> None:
        """
        当样本被拒绝时调用。

        :param reader: 触发事件的数据读取器。
        :param status: 样本拒绝状态。
        """

    def on_requested_incompatible_qos(self, reader: DataReader, status: RequestedIncompatibleQosStatus) -> None:
        """
        当请求的 QoS 不兼容时调用。

        :param reader: 触发事件的数据读取器。
        :param status: QoS 不兼容状态。
        """

    def on_subscription_matched(self, reader: DataReader, status: SubscriptionMatchedStatus) -> None:
        """
        当订阅匹配时调用。

        :param reader: 触发事件的数据读取器。
        :param status: 订阅匹配状态。
        """

    def on_sample_lost(self, reader: DataReader, status: SampleLostStatus) -> None:
        """
        当样本丢失时调用。

        :param reader: 触发事件的数据读取器。
        :param status: 样本丢失状态。
        """


class SimpleDataReaderListener(Generic[T, TSeq, TDataReader], DataReaderListener):
    """
    简单数据读取器监听器。

    提供简化接口的数据读取器监听器，支持泛型类型。
    """

    def __init__(self) -> None:
        """初始化简单数据读取器监听器。"""

    def on_process_sample(self, reader: DataReader, sample: T, info: SampleInfo) -> None:
        """
        处理样本数据。

        :param reader: 数据读取器。
        :param sample: 要处理的样本数据。
        :param info: 样本信息。
        """


class DataWriterListener(Listener):
    """
    数据写入器监听器。

    处理数据写入器相关事件的监听器。
    """

    def __init__(self) -> None:
        """初始化数据写入器监听器。"""

    def on_liveliness_lost(self, the_writer: DataWriter, status: LivelinessLostStatus) -> None:
        """
        当活跃性丢失时调用。

        :param the_writer: 触发事件的数据写入器。
        :param status: 活跃性丢失状态。
        """

    def on_offered_deadline_missed(self, the_writer: DataWriter, status: OfferedDeadlineMissedStatus) -> None:
        """
        当提供的截止期限错过时调用。

        :param the_writer: 触发事件的数据写入器。
        :param status: 截止期限错过状态。
        """

    def on_offered_incompatible_qos(self, the_writer: DataWriter, status: OfferedIncompatibleQosStatus) -> None:
        """
        当提供的 QoS 不兼容时调用。

        :param the_writer: 触发事件的数据写入器。
        :param status: QoS 不兼容状态。
        """

    def on_publication_matched(self, the_writer: DataWriter, status: PublicationMatchedStatus) -> None:
        """
        当发布匹配时调用。

        :param the_writer: 触发事件的数据写入器。
        :param status: 发布匹配状态。
        """


class PublisherListener(DataWriterListener):
    """
    发布者监听器。

    处理发布者相关事件的监听器，继承自数据写入器监听器。
    """

    def __init__(self) -> None:
        """初始化发布者监听器。"""


class SubscriberListener(DataReaderListener):
    """
    订阅者监听器。

    处理订阅者相关事件的监听器，继承自数据读取器监听器。
    """

    def __init__(self) -> None:
        """初始化订阅者监听器。"""

    def on_data_on_readers(self, the_subscriber: Subscriber) -> None:
        """
        当订阅者有数据时调用。

        :param the_subscriber: 触发事件的订阅者。
        """


class TopicListener(Listener):
    """
    主题监听器。

    处理主题相关事件的监听器。
    """

    def __init__(self) -> None:
        """初始化主题监听器。"""

    def on_inconsistent_topic(self, the_topic: Topic, status: InconsistentTopicStatus) -> None:
        """
        当主题不一致时调用。

        :param the_topic: 触发事件的主题。
        :param status: 不一致主题状态。
        """


class DomainParticipantListener(PublisherListener, TopicListener, SubscriberListener):
    """
    域参与者监听器。

    处理域参与者相关事件的监听器，多重继承自发布者、主题和订阅者监听器。
    """

    def __init__(self) -> None:
        """初始化域参与者监听器。"""

    def on_domain_received(self) -> None:
        """当接收到域数据时调用。"""




class TrainCmd:
    """
    训练命令数据结构。

    用于传输训练相关的命令和控制信息。
    """

    def __init__(self) -> None:
        """初始化训练命令。"""

    round_id: int
    """训练轮次ID。"""

    subset_size: int
    """子集大小。"""

    epochs: int
    """训练轮数。"""

    lr: float
    """学习率。"""

    seed: int
    """随机种子。"""


class ClientUpdate:
    """
    客户端更新数据结构。

    用于传输客户端训练更新信息。
    """

    def __init__(self) -> None:
        """初始化客户端更新。"""

    client_id: int
    """客户端ID。"""

    round_id: int
    """训练轮次ID。"""

    num_samples: int
    """样本数量。"""

    @property
    def data(self) -> bytes:
        """获取数据内容（bytes类型）。"""

    @data.setter
    def data(self, value: bytes) -> None:
        """设置数据内容。"""


class ModelBlob:
    """
    模型二进制数据。

    用于传输模型参数的二进制数据。
    """

    def __init__(self) -> None:
        """初始化模型二进制数据。"""

    round_id: int
    """训练轮次ID。"""

    @property
    def data(self) -> bytes:
        """获取模型数据（bytes类型）。"""

    @data.setter
    def data(self, value: bytes) -> None:
        """设置模型数据。"""


class TrainCmdSeq:
    """
    训练命令序列。

    用于存储多个训练命令的序列容器。
    """

    def __init__(self, max: int = 16) -> None:
        """
        初始化训练命令序列。

        :param max: 最大容量，默认为16。
        """

    def length(self) -> int:
        """获取序列长度。"""

    def get_at(self, i: int) -> TrainCmd:
        """
        获取指定索引的训练命令。

        :param i: 索引位置。
        :return: 训练命令对象。
        """

    def set_at(self, i: int, val: TrainCmd) -> None:
        """
        设置指定索引的训练命令。

        :param i: 索引位置。
        :param val: 训练命令值。
        """

    def append(self, val: TrainCmd) -> None:
        """
        添加训练命令到序列末尾。

        :param val: 要添加的训练命令。
        """

    def clear(self) -> None:
        """清空序列。"""

    def ensure_length(self, length: int, max: int) -> None:
        """
        确保序列具有指定长度和最大容量。

        :param length: 目标长度。
        :param max: 最大容量。
        """

    def to_array(self) -> List[TrainCmd]:
        """将序列转换为Python列表。"""

    def from_array(self, list: List[TrainCmd]) -> bool:
        """
        从Python列表复制数据到序列中。

        :param list: 源列表。
        :return: 成功返回True。
        """


class ClientUpdateSeq:
    """
    客户端更新序列。

    用于存储多个客户端更新的序列容器。
    """

    def __init__(self, max: int = 16) -> None:
        """
        初始化客户端更新序列。

        :param max: 最大容量，默认为16。
        """

    def length(self) -> int:
        """获取序列长度。"""

    def get_at(self, i: int) -> ClientUpdate:
        """
        获取指定索引的客户端更新。

        :param i: 索引位置。
        :return: 客户端更新对象。
        """

    def set_at(self, i: int, val: ClientUpdate) -> None:
        """
        设置指定索引的客户端更新。

        :param i: 索引位置。
        :param val: 客户端更新值。
        """

    def append(self, val: ClientUpdate) -> None:
        """
        添加客户端更新到序列末尾。

        :param val: 要添加的客户端更新。
        """

    def clear(self) -> None:
        """清空序列。"""

    def ensure_length(self, length: int, max: int) -> None:
        """
        确保序列具有指定长度和最大容量。

        :param length: 目标长度。
        :param max: 最大容量。
        """

    def to_array(self) -> List[ClientUpdate]:
        """将序列转换为Python列表。"""

    def from_array(self, list: List[ClientUpdate]) -> bool:
        """
        从Python列表复制数据到序列中。

        :param list: 源列表。
        :return: 成功返回True。
        """


class ModelBlobSeq:
    """
    模型二进制数据序列。

    用于存储多个模型二进制数据的序列容器。
    """

    def __init__(self, max: int = 16) -> None:
        """
        初始化模型二进制数据序列。

        :param max: 最大容量，默认为16。
        """

    def length(self) -> int:
        """获取序列长度。"""

    def get_at(self, i: int) -> ModelBlob:
        """
        获取指定索引的模型二进制数据。

        :param i: 索引位置。
        :return: 模型二进制数据对象。
        """

    def set_at(self, i: int, val: ModelBlob) -> None:
        """
        设置指定索引的模型二进制数据。

        :param i: 索引位置。
        :param val: 模型二进制数据值。
        """

    def append(self, val: ModelBlob) -> None:
        """
        添加模型二进制数据到序列末尾。

        :param val: 要添加的模型二进制数据。
        """

    def clear(self) -> None:
        """清空序列。"""

    def ensure_length(self, length: int, max: int) -> None:
        """
        确保序列具有指定长度和最大容量。

        :param length: 目标长度。
        :param max: 最大容量。
        """

    def to_array(self) -> List[ModelBlob]:
        """将序列转换为Python列表。"""

    def from_array(self, list: List[ModelBlob]) -> bool:
        """
        从Python列表复制数据到序列中。

        :param list: 源列表。
        :return: 成功返回True。
        """


class TrainCmdDataWriter(DataWriter):
    """
    训练命令数据写入器。

    用于写入训练命令数据到DDS域。
    """

    def write(self, msg: TrainCmd) -> ReturnCode_t:
        """
        写入训练命令数据。

        :param msg: 要写入的训练命令。
        :return: 返回码。
        """


class ClientUpdateDataWriter(DataWriter):
    """
    客户端更新数据写入器。

    用于写入客户端更新数据到DDS域。
    """

    def write(self, msg: ClientUpdate) -> ReturnCode_t:
        """
        写入客户端更新数据。

        :param msg: 要写入的客户端更新。
        :return: 返回码。
        """


class ModelBlobDataWriter(DataWriter):
    """
    模型二进制数据写入器。

    用于写入模型二进制数据到DDS域。
    """

    def write(self, msg: ModelBlob) -> ReturnCode_t:
        """
        写入模型二进制数据。

        :param msg: 要写入的模型二进制数据。
        :return: 返回码。
        """


class TrainCmdDataReader(DataReader):
    """
    训练命令数据读取器。

    用于从DDS域读取训练命令数据。
    """

    def read(
            self,
            dataSeq: TrainCmdSeq,
            infoSeq: SampleInfoSeq,
            max_samples: int = -1,
            sampleState: SampleStateMask = ANY_SAMPLE_STATE,
            viewState: ViewStateMask = ANY_VIEW_STATE,
            instanceState: InstanceStateMask = ANY_INSTANCE_STATE,
    ) -> ReturnCode_t:
        """
        读取训练命令数据。

        :param dataSeq: 输出数据序列。
        :param infoSeq: 输出样本信息序列。
        :param max_samples: 最大样本数，-1表示无限制。
        :param sampleState: 样本状态掩码。
        :param viewState: 视图状态掩码。
        :param instanceState: 实例状态掩码。
        :return: 返回码。
        """

    def take(
            self,
            dataSeq: TrainCmdSeq,
            infoSeq: SampleInfoSeq,
            max_samples: int = -1,
            sampleState: SampleStateMask = ANY_SAMPLE_STATE,
            viewState: ViewStateMask = ANY_VIEW_STATE,
            instanceState: InstanceStateMask = ANY_INSTANCE_STATE,
    ) -> ReturnCode_t:
        """
        获取训练命令数据（读取并移除）。

        :param dataSeq: 输出数据序列。
        :param infoSeq: 输出样本信息序列。
        :param max_samples: 最大样本数，-1表示无限制。
        :param sampleState: 样本状态掩码。
        :param viewState: 视图状态掩码。
        :param instanceState: 实例状态掩码。
        :return: 返回码。
        """

    def create_readcondition(
            self,
            sample_mask: SampleStateMask,
            view_mask: ViewStateMask,
            instance_mask: InstanceStateMask,
    ) -> Optional[ReadCondition]:
        """
        创建读取条件。

        :param sample_mask: 样本状态掩码。
        :param view_mask: 视图状态掩码。
        :param instance_mask: 实例状态掩码。
        :return: 读取条件对象。
        """

    def return_loan(self, dataSeq: TrainCmdSeq, infoSeq: SampleInfoSeq) -> ReturnCode_t:
        """
        归还数据贷款。

        :param dataSeq: 数据序列。
        :param infoSeq: 样本信息序列。
        :return: 返回码。
        """


class ClientUpdateDataReader(DataReader):
    """
    客户端更新数据读取器。

    用于从DDS域读取客户端更新数据。
    """

    def read(
            self,
            dataSeq: ClientUpdateSeq,
            infoSeq: SampleInfoSeq,
            max_samples: int = -1,
            sampleState: SampleStateMask = ANY_SAMPLE_STATE,
            viewState: ViewStateMask = ANY_VIEW_STATE,
            instanceState: InstanceStateMask = ANY_INSTANCE_STATE,
    ) -> ReturnCode_t:
        """
        读取客户端更新数据。

        :param dataSeq: 输出数据序列。
        :param infoSeq: 输出样本信息序列。
        :param max_samples: 最大样本数，-1表示无限制。
        :param sampleState: 样本状态掩码。
        :param viewState: 视图状态掩码。
        :param instanceState: 实例状态掩码。
        :return: 返回码。
        """

    def take(
            self,
            dataSeq: ClientUpdateSeq,
            infoSeq: SampleInfoSeq,
            max_samples: int = -1,
            sampleState: SampleStateMask = ANY_SAMPLE_STATE,
            viewState: ViewStateMask = ANY_VIEW_STATE,
            instanceState: InstanceStateMask = ANY_INSTANCE_STATE,
    ) -> ReturnCode_t:
        """
        获取客户端更新数据（读取并移除）。

        :param dataSeq: 输出数据序列。
        :param infoSeq: 输出样本信息序列。
        :param max_samples: 最大样本数，-1表示无限制。
        :param sampleState: 样本状态掩码。
        :param viewState: 视图状态掩码。
        :param instanceState: 实例状态掩码。
        :return: 返回码。
        """

    def create_readcondition(
            self,
            sample_mask: SampleStateMask,
            view_mask: ViewStateMask,
            instance_mask: InstanceStateMask,
    ) -> Optional[ReadCondition]:
        """
        创建读取条件。

        :param sample_mask: 样本状态掩码。
        :param view_mask: 视图状态掩码。
        :param instance_mask: 实例状态掩码。
        :return: 读取条件对象。
        """

    def return_loan(self, dataSeq: ClientUpdateSeq, infoSeq: SampleInfoSeq) -> ReturnCode_t:
        """
        归还数据贷款。

        :param dataSeq: 数据序列。
        :param infoSeq: 样本信息序列。
        :return: 返回码。
        """


class ModelBlobDataReader(DataReader):
    """
    模型二进制数据读取器。

    用于从DDS域读取模型二进制数据。
    """

    def read(
            self,
            dataSeq: ModelBlobSeq,
            infoSeq: SampleInfoSeq,
            max_samples: int = -1,
            sampleState: SampleStateMask = ANY_SAMPLE_STATE,
            viewState: ViewStateMask = ANY_VIEW_STATE,
            instanceState: InstanceStateMask = ANY_INSTANCE_STATE,
    ) -> ReturnCode_t:
        """
        读取模型二进制数据。

        :param dataSeq: 输出数据序列。
        :param infoSeq: 输出样本信息序列。
        :param max_samples: 最大样本数，-1表示无限制。
        :param sampleState: 样本状态掩码。
        :param viewState: 视图状态掩码。
        :param instanceState: 实例状态掩码。
        :return: 返回码。
        """

    def take(
            self,
            dataSeq: ModelBlobSeq,
            infoSeq: SampleInfoSeq,
            max_samples: int = -1,
            sampleState: SampleStateMask = ANY_SAMPLE_STATE,
            viewState: ViewStateMask = ANY_VIEW_STATE,
            instanceState: InstanceStateMask = ANY_INSTANCE_STATE,
    ) -> ReturnCode_t:
        """
        获取模型二进制数据（读取并移除）。

        :param dataSeq: 输出数据序列。
        :param infoSeq: 输出样本信息序列。
        :param max_samples: 最大样本数，-1表示无限制。
        :param sampleState: 样本状态掩码。
        :param viewState: 视图状态掩码。
        :param instanceState: 实例状态掩码。
        :return: 返回码。
        """

    def create_readcondition(
            self,
            sample_mask: SampleStateMask,
            view_mask: ViewStateMask,
            instance_mask: InstanceStateMask,
    ) -> Optional[ReadCondition]:
        """
        创建读取条件。

        :param sample_mask: 样本状态掩码。
        :param view_mask: 视图状态掩码。
        :param instance_mask: 实例状态掩码。
        :return: 读取条件对象。
        """

    def return