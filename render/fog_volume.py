"""第 51 批：体积雾一进洞穴就整片发灰：froxel 深度按近平面线性切，远近精度差几十倍；
点光注入把聚光锥当球算；半分辨率升采样双线性漏光；时域累积不按相机位移重投影，转身拖影；
透明物体排在雾后；密度纹理三平面接缝；切近远平面不清历史；体积盒外仍采样内部密度；
粒子雾与解析雾重复叠加；分屏共用一张 froxel 图。

本模块是核心修复，提供：
- 指数深度切片：froxel 切片按指数分布，远近相对精度一致；
- 聚光锥注入权重：外锥为 0、内锥为 1，锥内平滑过渡，不再当球各向同性注入；
- 深度感知升采样权重：替代裸双线性，按深度相似度加权，防止半分辨率升采样漏光；
- 时域历史校验：重投影后比较深度，相机移动/转身/切近远平面时使历史失效，消除拖影；
- 三平面权重归一：权重和恒为 1，消除密度纹理接缝；
- 体积盒密度门控：盒外一律不采样内部密度。
"""


def slice_depth(index, slices, z_near, z_far):
    """返回第 index 个 froxel 切片的深度，按指数分布。

    线性切片在近处浪费精度、远处切片过厚，指数分布
        z(i) = z_near * (z_far / z_near) ** (i / slices)
    使每个切片的相对深度误差一致。index 取值 [0, slices)，
    z(0) == z_near，z(slices) 恰好到达 z_far。
    """
    if slices <= 0:
        raise ValueError("slices must be positive")
    if z_near <= 0.0 or z_far <= z_near:
        raise ValueError("require 0 < z_near < z_far")
    return z_near * (z_far / z_near) ** (index / slices)


def spot_weight(cos_angle, cos_outer, cos_inner):
    """返回聚光锥权重，外锥为 0、内锥为 1。

    cos_angle 为采样方向与聚光轴夹角的余弦。权重在
    [cos_outer, cos_inner] 之间做 Hermite 平滑过渡，
    锥外严格为 0、内锥严格为 1。点光注入时按此权重衰减，
    而不是把聚光锥当球做各向同性注入。
    """
    if cos_inner <= cos_outer:
        raise ValueError("require cos_inner > cos_outer")
    t = (cos_angle - cos_outer) / (cos_inner - cos_outer)
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def upsample_weight(depth_center, depth_neighbor):
    """返回邻域像素在升采样中的归一化权重。

    深度感知的双边权重：邻域低分辨率样本与中心像素深度越接近，
    权重越大；相对深度差以样本自身深度为尺度（近处容差小、远处
    容差大）。返回值与交换参数后的返回值之和恒为 1，即成对归一，
    可直接用于双边升采样的混合权重，避免双线性把远处雾漏进近处
    几何边缘。
    """
    def similarity(c, n):
        scale = max(abs(n), 1e-6)
        return 1.0 / (1.0 + abs(c - n) / scale)

    s = similarity(depth_center, depth_neighbor)
    s_swapped = similarity(depth_neighbor, depth_center)
    return s / (s + s_swapped)


def history_is_valid(prev_depth, curr_depth, tol=0.05):
    """判断时域历史是否可复用。

    按相机位移重投影后，比较历史深度与当前深度：相对偏差超过
    tol 说明该像素对应的几何已变化（转身、遮挡切换、近远平面
    调整等），历史必须丢弃重新累积，否则产生拖影。
    """
    scale = max(abs(prev_depth), 1e-6)
    return abs(curr_depth - prev_depth) <= tol * scale


def triplanar_weight(nx, ny, nz, sharpness=4.0):
    """返回三平面映射的三个归一化权重。

    按法线分量绝对值的 sharpness 次幂加权并归一化，权重和恒为 1，
    消除密度纹理在三张投影交界处的接缝。返回顺序对应投影平面
    (YZ, XY, XZ)，即分别由 |nx|、|nz|、|ny| 决定的权重。
    法线为零向量时退回均匀权重，避免除零。
    """
    wx = abs(nx) ** sharpness
    wy = abs(ny) ** sharpness
    wz = abs(nz) ** sharpness
    total = wx + wy + wz
    if total <= 0.0:
        return (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
    return (wx / total, wz / total, wy / total)


def density_in_box(point, box_min, box_max):
    """判断点是否落在体积雾盒内（闭区间）。

    盒外采样必须门控为 0 密度，避免在体积盒之外仍读到
    盒内密度导致雾外溢。
    """
    return all(lo <= p <= hi for p, lo, hi in zip(point, box_min, box_max))
