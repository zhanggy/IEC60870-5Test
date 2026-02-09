"""
IEC60870-5-104协议常量定义
"""


# APCI类型定义
class APCIType:
    """APCI帧类型"""
    I_FORMAT = 0  # I格式 (信息传输)
    S_FORMAT = 1  # S格式 (监视功能)
    U_FORMAT = 3  # U格式 (未编号控制功能)


# U格式功能码
class UType:
    """U格式控制功能"""
    STARTDT_ACT = 0x07    # 启动数据传输激活
    STARTDT_CON = 0x0B    # 启动数据传输确认
    STOPDT_ACT = 0x13     # 停止数据传输激活
    STOPDT_CON = 0x23     # 停止数据传输确认
    TESTFR_ACT = 0x43     # 测试帧激活
    TESTFR_CON = 0x83     # 测试帧确认


# TypeID - 类型标识
class TypeID:
    """ASDU类型标识"""
    # 监视方向的过程信息
    M_SP_NA_1 = 1   # 单点信息
    M_SP_TA_1 = 2   # 带时标的单点信息
    M_DP_NA_1 = 3   # 双点信息
    M_DP_TA_1 = 4   # 带时标的双点信息
    M_ST_NA_1 = 5   # 步位置信息
    M_ST_TA_1 = 6   # 带时标的步位置信息
    M_BO_NA_1 = 7   # 比特串
    M_BO_TA_1 = 8   # 带时标的比特串
    M_ME_NA_1 = 9   # 测量值，归一化值
    M_ME_TA_1 = 10  # 测量值，带时标的归一化值
    M_ME_NB_1 = 11  # 测量值，标度化值
    M_ME_TB_1 = 12  # 测量值，带时标的标度化值
    M_ME_NC_1 = 13  # 测量值，短浮点数
    M_ME_TC_1 = 14  # 测量值，带时标的短浮点数
    M_IT_NA_1 = 15  # 累计量
    M_IT_TA_1 = 16  # 带时标的累计量

    # 控制方向的过程命令
    C_SC_NA_1 = 45  # 单点命令
    C_DC_NA_1 = 46  # 双点命令
    C_RC_NA_1 = 47  # 调节步命令
    C_SE_NA_1 = 48  # 设置命令，归一化值
    C_SE_NB_1 = 49  # 设置命令，标度化值
    C_SE_NC_1 = 50  # 设置命令，短浮点数

    # 监视方向的系统命令
    M_EI_NA_1 = 70  # 初始化结束

    # 控制方向的系统命令
    C_IC_NA_1 = 100  # 总召唤命令
    C_CI_NA_1 = 101  # 计数量召唤命令
    C_RD_NA_1 = 102  # 读命令
    C_CS_NA_1 = 103  # 时钟同步命令
    C_TS_NA_1 = 104  # 测试命令
    C_RP_NA_1 = 105  # 复位进程命令

    # 文件传输
    F_FR_NA_1 = 120  # 文件准备就绪
    F_SR_NA_1 = 121  # 节准备就绪
    F_SC_NA_1 = 122  # 召唤目录，选择文件，召唤文件，召唤节
    F_LS_NA_1 = 123  # 最后的节，最后的段
    F_AF_NA_1 = 124  # 确认文件，确认节
    F_SG_NA_1 = 125  # 段
    F_DR_TA_1 = 126  # 目录


# 传送原因COT
class COT:
    """传送原因"""
    PERIODIC = 1          # 周期/循环
    BACK = 2              # 背景扫描
    SPONT = 3             # 突发/自发
    INIT = 4              # 初始化
    REQ = 5               # 请求或被请求
    ACT = 6               # 激活
    ACTCON = 7            # 激活确认
    DEACT = 8             # 停止激活
    DEACTCON = 9          # 停止激活确认
    ACTTERM = 10          # 激活终止
    RETREM = 11           # 远方命令引起的返送信息
    RETLOC = 12           # 当地命令引起的返送信息
    FILE = 13             # 文件传输
    INROGEN = 20          # 响应站总召唤
    INRO1 = 21            # 响应第1组召唤
    INRO16 = 36           # 响应第16组召唤
    REQCOGEN = 37         # 响应计数量站总召唤
    REQCO1 = 38           # 响应第1组计数量召唤
    REQCO4 = 41           # 响应第4组计数量召唤
    UNKNOWNTYPE = 44      # 未知的类型标识
    UNKNOWNCOT = 45       # 未知的传送原因
    UNKNOWNCA = 46        # 未知的应用服务数据单元公共地址
    UNKNOWNIOA = 47       # 未知的信息对象地址


# 品质描述词QDS
class QDS:
    """品质描述词标志位"""
    OVERFLOW = 0x01       # 溢出OV
    BLOCKED = 0x10        # 被封锁BL
    SUBSTITUTED = 0x20    # 取代SB
    NOT_TOPICAL = 0x40    # 不当NT
    INVALID = 0x80        # 无效IV


# 单点命令限定词
class SCO:
    """单点命令限定词"""
    OFF = 0x00
    ON = 0x01
    SELECT = 0x80         # 选择/执行标志


# 双点命令限定词
class DCO:
    """双点命令限定词"""
    NOT_PERMITTED = 0x00  # 未被允许
    OFF = 0x01            # 分
    ON = 0x02             # 合
    NOT_PERMITTED_2 = 0x03  # 未被允许
    SELECT = 0x80         # 选择/执行标志


# 协议常量
class ProtocolConstants:
    """协议相关常量"""
    APCI_START_BYTE = 0x68  # APCI起始字节
    APCI_MIN_LENGTH = 6      # APCI最小长度
    ASDU_MIN_LENGTH = 2      # ASDU最小长度

    DEFAULT_T0 = 30  # 连接建立超时(秒)
    DEFAULT_T1 = 15  # 发送或测试APDU的超时(秒)
    DEFAULT_T2 = 10  # 无数据报文t2<t1时，确认接收序号的超时(秒)
    DEFAULT_T3 = 20  # 长期空闲状态下发送测试帧的超时(秒)
    DEFAULT_K = 12   # 最大未确认I帧数量
    DEFAULT_W = 8    # 最新确认后最多接收I帧数量
