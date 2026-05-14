"""
Canvas 图表绘制工具 - 用于看板可视化
支持：折线图、柱状图、饼图、雷达图、横向条状排行
"""
import math
import tkinter as tk


def draw_line_chart(canvas, data, x_key, y_key, title="",
                    color="#4472C4", fill_color="#D6E4F0",
                    margin=(50, 25, 20, 35)):
    """绘制折线趋势图"""
    cw = max(canvas.winfo_width(), 250)
    ch = max(canvas.winfo_height(), 100)
    canvas.delete("all")

    if not data or len(data) < 2:
        canvas.create_text(cw / 2, ch / 2, text="数据不足", fill="#CCCCCC",
                           font=("微软雅黑", 12))
        return

    ml, mt, mr, mb = margin
    plot_w = cw - ml - mr
    plot_h = ch - mt - mb

    values = []
    for d in data:
        v = d.get(y_key, 0)
        try:
            values.append(float(v) if v else 0)
        except (ValueError, TypeError):
            values.append(0)

    max_val = max(values) if max(values) > 0 else 1
    min_val = min(values)
    val_range = max_val - min_val if max_val != min_val else max_val
    labels = [str(d.get(x_key, "")) for d in data]
    n = len(values)

    # 坐标轴
    canvas.create_line(ml, mt, ml, mt + plot_h, fill="#CCCCCC", width=1)
    canvas.create_line(ml, mt + plot_h, ml + plot_w, mt + plot_h,
                       fill="#CCCCCC", width=1)

    # Y 轴刻度（4格）
    for i in range(5):
        y_val = max_val - (max_val - min_val) * i / 4
        y = mt + plot_h * i / 4
        canvas.create_text(ml - 5, y, anchor="e", text=f"{y_val:,.0f}",
                           fill="#999999", font=("微软雅黑", 7))

    # 计算数据点
    points = []
    for i in range(n):
        x = ml + plot_w * i / (n - 1) if n > 1 else ml + plot_w / 2
        if val_range > 0:
            y = mt + plot_h * (1 - (values[i] - min_val) / val_range)
        else:
            y = mt + plot_h / 2
        points.append((x, y))

    # 填充区域
    fill_points = [points[0][0], mt + plot_h]
    for px, py in points:
        fill_points.extend([px, py])
    fill_points.extend([points[-1][0], mt + plot_h])
    canvas.create_polygon(fill_points, fill=fill_color, outline="", width=0)

    # 折线
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        canvas.create_line(x1, y1, x2, y2, fill=color, width=2, smooth=True)

    # 数据点 + 值标签
    for i, (px, py) in enumerate(points):
        canvas.create_oval(px - 3, py - 3, px + 3, py + 3,
                           fill="white", outline=color, width=2)
        if values[i] > 0:
            canvas.create_text(px, py - 10, anchor="s",
                               text=f"{values[i]:,.0f}" if values[i] >= 10000 else str(values[i]),
                               fill="#333333", font=("微软雅黑", 7, "bold"))

    # X 轴标签
    for i in range(n):
        x = ml + plot_w * i / (n - 1) if n > 1 else ml + plot_w / 2
        label = labels[i]
        if len(label) > 5:
            label = label[-5:]
        canvas.create_text(x, mt + plot_h + 12, text=label,
                           fill="#999999", font=("微软雅黑", 7),
                           angle=0 if n <= 10 else 45)

    # 标题
    if title:
        canvas.create_text(ml + 5, mt - 2, anchor="nw", text=title,
                           fill="#555555", font=("微软雅黑", 9, "bold"))


def draw_bar_chart(canvas, data, x_key, y_key, title="",
                   colors=("#4472C4", "#ED7D31"), margin=(50, 25, 20, 35)):
    """绘制柱状图 - 支持多系列"""
    cw = max(canvas.winfo_width(), 250)
    ch = max(canvas.winfo_height(), 100)
    canvas.delete("all")

    if not data or len(data) < 2:
        canvas.create_text(cw / 2, ch / 2, text="数据不足", fill="#CCCCCC",
                           font=("微软雅黑", 12))
        return

    ml, mt, mr, mb = margin
    plot_w = cw - ml - mr
    plot_h = ch - mt - mb

    values = []
    for d in data:
        v = d.get(y_key, 0)
        try:
            values.append(float(v) if v else 0)
        except (ValueError, TypeError):
            values.append(0)

    max_val = max(values) if max(values) > 0 else 1
    n = len(values)
    labels = [str(d.get(x_key, "")) for d in data]

    # 坐标轴
    canvas.create_line(ml, mt, ml, mt + plot_h, fill="#CCCCCC", width=1)
    canvas.create_line(ml, mt + plot_h, ml + plot_w, mt + plot_h,
                       fill="#CCCCCC", width=1)

    # Y 轴刻度
    for i in range(5):
        y_val = max_val * (4 - i) / 4
        y = mt + plot_h * i / 4
        canvas.create_text(ml - 5, y, anchor="e", text=f"{y_val:,.0f}",
                           fill="#999999", font=("微软雅黑", 7))

    # 柱体
    bar_w = min(plot_w / (n * 1.8), 35)
    gap = (plot_w - bar_w * n) / (n + 1)

    for i in range(n):
        val = values[i]
        bar_h = val / max_val * plot_h
        x = ml + gap + i * (bar_w + gap)
        y = mt + plot_h - bar_h

        color_i = colors[i % len(colors)] if isinstance(colors, list) else colors
        canvas.create_rectangle(x, y, x + bar_w, mt + plot_h,
                                fill=color_i, outline=color_i, width=0)

        if val > 0:
            canvas.create_text(x + bar_w / 2, y - 4, anchor="s",
                               text=f"{val:,.0f}", fill="#333333",
                               font=("微软雅黑", 7, "bold"))

        label = labels[i]
        if len(label) > 5:
            label = label[-5:]
        canvas.create_text(x + bar_w / 2, mt + plot_h + 12, text=label,
                           fill="#999999", font=("微软雅黑", 7),
                           angle=0 if n <= 10 else 45)

    if title:
        canvas.create_text(ml + 5, mt - 2, anchor="nw", text=title,
                           fill="#555555", font=("微软雅黑", 9, "bold"))


def draw_pie_chart(canvas, data, label_key="label", value_key="value",
                   title="", margin=(10, 25, 10, 15)):
    """绘制饼图"""
    cw = max(canvas.winfo_width(), 200)
    ch = max(canvas.winfo_height(), 150)
    canvas.delete("all")

    if not data:
        canvas.create_text(cw / 2, ch / 2, text="暂无数据", fill="#CCCCCC",
                           font=("微软雅黑", 12))
        return

    items = []
    total = 0
    for d in data:
        v = d.get(value_key, 0)
        try:
            v = float(v) if v else 0
        except (ValueError, TypeError):
            v = 0
        items.append((str(d.get(label_key, "")), v))
        total += v

    if total <= 0:
        canvas.create_text(cw / 2, ch / 2, text="暂无数据", fill="#CCCCCC",
                           font=("微软雅黑", 12))
        return

    # 饼图颜色
    pie_colors = ["#4472C4", "#ED7D31", "#70AD47", "#FFC000",
                  "#5B9BD5", "#9B59B6", "#1ABC9C", "#E74C3C",
                  "#2E75B6", "#BF8F00", "#548235", "#C55A11"]

    # 筛掉占比 < 2% 的合并为"其他"
    main_items = [(l, v) for l, v in items if v / total >= 0.02]
    other_sum = sum(v for l, v in items if v / total < 0.02)
    if other_sum > 0:
        main_items.append(("其他", other_sum))

    cx = cw * 0.38
    cy = ch / 2 + 5
    radius = min(cx - margin[0] - 10, cy - margin[1] - 10,
                 ch - cy - margin[3] - 10) - 5
    radius = max(radius, 30)

    # 绘制饼图
    start_angle = 90
    for i, (label, val) in enumerate(main_items):
        angle = val / total * 360
        color = pie_colors[i % len(pie_colors)]
        canvas.create_arc(cx - radius, cy - radius,
                          cx + radius, cy + radius,
                          start=start_angle, extent=angle,
                          fill=color, outline="white", width=1)
        start_angle += angle

    # 图例（右侧）
    lx = cw * 0.72
    ly = margin[1] + 8
    legend_w = cw - lx - margin[2]

    start_angle = 90
    for i, (label, val) in enumerate(main_items):
        color = pie_colors[i % len(pie_colors)]
        pct = val / total * 100

        canvas.create_rectangle(lx, ly, lx + 8, ly + 8,
                                fill=color, outline="")
        display_label = label if len(label) <= 6 else label[:6] + ".."
        canvas.create_text(lx + 12, ly + 4, anchor="w",
                           text=f"{display_label}  {pct:.1f}%",
                           fill="#555555", font=("微软雅黑", 8))
        ly += 18

        if ly > ch - 10:
            break

    if title:
        canvas.create_text(cw / 2, 3, anchor="n", text=title,
                           fill="#555555", font=("微软雅黑", 9, "bold"))


def draw_radar_chart(canvas, data, label_key="label", series_key="value",
                     title="", max_val=None, margin=(30, 25, 10, 15)):
    """绘制雷达图"""
    cw = max(canvas.winfo_width(), 200)
    ch = max(canvas.winfo_height(), 160)
    canvas.delete("all")

    if not data or len(data) < 3:
        canvas.create_text(cw / 2, ch / 2, text="数据不足（至少3项）",
                           fill="#CCCCCC", font=("微软雅黑", 12))
        return

    items = []
    for d in data:
        v = d.get(series_key, 0)
        try:
            v = float(v) if v else 0
        except (ValueError, TypeError):
            v = 0
        items.append((str(d.get(label_key, "")), v))

    values = [v for _, v in items]
    labels = [l for l, _ in items]
    max_v = max_val or max(values) * 1.1
    if max_v <= 0:
        max_v = 1
    n = len(items)
    cx = cw / 2
    cy = ch / 2 + 3
    radius = min(cw / 2 - margin[0], ch / 2 - margin[1] - 5) - 5
    radius = max(radius, 40)

    # 网格（4圈）
    for level in range(1, 5):
        r = radius * level / 4
        points = []
        for i in range(n):
            angle = math.pi / 2 - 2 * math.pi * i / n
            points.extend([cx + r * math.cos(angle), cy - r * math.sin(angle)])
        canvas.create_polygon(points, outline="#E0E0E0", fill="",
                              width=1 if level < 4 else 2)

    # 轴线
    for i in range(n):
        angle = math.pi / 2 - 2 * math.pi * i / n
        canvas.create_line(cx, cy, cx + radius * math.cos(angle),
                           cy - radius * math.sin(angle),
                           fill="#E0E0E0", width=1)

    # 数据区域
    points = []
    for i in range(n):
        angle = math.pi / 2 - 2 * math.pi * i / n
        v = values[i] / max_v if max_v > 0 else 0
        r = radius * min(v, 1)
        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        points.append((x, y))

    # 填充
    poly_coords = []
    for x, y in points:
        poly_coords.extend([x, y])
    if poly_coords:
        canvas.create_polygon(poly_coords, fill="#4472C4", stipple="gray25",
                              outline="#4472C4", width=2)

    # 数据点 + 标签
    for i, (x, y) in enumerate(points):
        canvas.create_oval(x - 3, y - 3, x + 3, y + 3,
                           fill="white", outline="#4472C4", width=2)

        angle = math.pi / 2 - 2 * math.pi * i / n
        label_x = cx + (radius + 5) * math.cos(angle)
        label_y = cy - (radius + 5) * math.sin(angle)
        anchor = "center"
        if angle > math.pi * 0.8 or angle < math.pi * 0.2:
            anchor = "center"
        elif math.pi * 0.2 <= angle < math.pi * 0.8:
            anchor = "w" if angle < math.pi / 2 else "e"
        canvas.create_text(label_x, label_y, text=labels[i],
                           fill="#555555", font=("微软雅黑", 8),
                           anchor=anchor)

        # 数值
        canvas.create_text(x, y - 8, anchor="s",
                           text=f"{values[i]:.0f}",
                           fill="#333333", font=("微软雅黑", 7, "bold"))

    if title:
        canvas.create_text(cw / 2, 3, anchor="n", text=title,
                           fill="#555555", font=("微软雅黑", 9, "bold"))


def draw_horizontal_bar(canvas, data, label_key, value_key, title="",
                        color="#4472C4", max_val=None, bar_height=20,
                        margin=(70, 25, 15, 15)):
    """绘制横向条状排行图"""
    cw = max(canvas.winfo_width(), 250)
    ch = max(canvas.winfo_height(), 100)
    canvas.delete("all")

    if not data:
        canvas.create_text(cw / 2, ch / 2, text="暂无排行数据",
                           fill="#CCCCCC", font=("微软雅黑", 12))
        return

    items = []
    for d in data:
        v = d.get(value_key, 0)
        try:
            v = float(v) if v else 0
        except (ValueError, TypeError):
            v = 0
        items.append((str(d.get(label_key, "")), v, d.get("color", color)))

    max_v = max_val or max(v for _, v, _ in items) or 1
    ml = margin[0]
    mt = margin[1]
    mr = margin[2]
    mb = margin[3]
    plot_w = cw - ml - mr
    total_h = ch - mt - mb
    n = len(items)
    gap = max(3, (total_h - n * bar_height) / (n + 1))

    # 排名圆点颜色
    rank_colors = ["#FFD700", "#C0C0C0", "#CD7F32", "#4472C4",
                   "#4472C4", "#4472C4", "#4472C4", "#4472C4",
                   "#4472C4", "#4472C4"]

    for i, (label, val, clr) in enumerate(items):
        y = mt + gap + i * (bar_height + gap)
        bar_w = (val / max_v) * (plot_w - 30) if max_v > 0 else 0
        clr = rank_colors[i] if i < len(rank_colors) else "#4472C4"

        # 排名序号
        canvas.create_text(ml - 50, y + bar_height / 2, anchor="e",
                           text=f"#{i+1}", fill="#999999",
                           font=("微软雅黑", 8, "bold"))

        # 标签
        display_label = label if len(label) <= 6 else label[:6] + ".."
        canvas.create_text(ml - 5, y + bar_height / 2, anchor="e",
                           text=display_label, fill="#333333",
                           font=("微软雅黑", 8))

        # 条状
        canvas.create_rectangle(ml, y, ml + bar_w, y + bar_height,
                                fill=clr, outline=clr, width=0)

        # 数值
        canvas.create_text(ml + bar_w + 4, y + bar_height / 2, anchor="w",
                           text=f"{val:,.0f}", fill="#555555",
                           font=("微软雅黑", 8, "bold"))

    if title:
        canvas.create_text(cw / 2, 3, anchor="n", text=title,
                           fill="#555555", font=("微软雅黑", 9, "bold"))
