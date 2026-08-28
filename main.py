import pygame
import json
import os
from datetime import datetime

# ===== 配置 =====
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
HOLD_THRESHOLD = 500
DATA_FILE = "solve_times.json"
ITEMS_PER_PAGE = 8

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
LIGHT_GRAY = (230, 230, 230)
DARK_GRAY = (100, 100, 100)
BLUE = (50, 150, 255)
RED = (255, 50, 50)
DELETE_COLOR = (200, 50, 50)
EDIT_COLOR = (50, 150, 255)
GREEN = (50, 200, 50)
DIALOG_BG = (240, 240, 240)

# ===== 数据管理 =====
def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                if data and isinstance(data[0], (int, float)):
                    new_data = [{"time": "--", "value": v} for v in data]
                    save_data(new_data)
                    return new_data
                elif data and isinstance(data[0], dict):
                    return data
                else:
                    return []
            else:
                return []
        except:
            return []

def save_data(times):
    with open(DATA_FILE, "w") as f:
        json.dump(times, f, indent=2, ensure_ascii=False)

# ===== Pygame 绘图辅助 =====
def draw_text(surface, text, font, color, rect, align="center"):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect()
    if align == "center":
        text_rect.center = rect.center
    elif align == "topleft":
        text_rect.topleft = rect.topleft
    elif align == "topright":
        text_rect.topright = rect.topright
    surface.blit(text_surf, text_rect)

def get_chinese_font(size):
    candidates = ['simhei', 'microsoft yahei', 'SimHei', 'Microsoft YaHei', 'STHeiti', 'Noto Sans CJK SC']
    for name in candidates:
        try:
            font = pygame.font.SysFont(name, size)
            if font.render('中', True, (0,0,0)).get_width() > 0:
                return font
        except:
            continue
    return pygame.font.Font(None, size)

def draw_chart(surface, font, times, chart_rect):
    x, y, w, h = chart_rect
    pygame.draw.rect(surface, WHITE, chart_rect)
    pygame.draw.rect(surface, BLACK, chart_rect, 1)

    values = [rec['value'] for rec in times]
    if len(values) < 2:
        draw_text(surface, "至少需要2次数据", font, DARK_GRAY, chart_rect)
        return

    min_val = 0
    max_val = max(values)
    if max_val == 0:
        max_val = 1
    max_val *= 1.1
    padding = 10
    plot_x0 = x + padding
    plot_y0 = y + padding
    plot_w = w - 2*padding
    plot_h = h - 2*padding

    points = []
    for idx, val in enumerate(values):
        px = plot_x0 + plot_w * (idx / (len(values)-1))
        py = plot_y0 + plot_h * (1 - (val - min_val) / (max_val - min_val))
        points.append((px, py))

    if len(points) > 1:
        pygame.draw.lines(surface, BLUE, False, points, 2)
    for pt in points:
        pygame.draw.circle(surface, RED, (int(pt[0]), int(pt[1])), 4)

    draw_text(surface, f"{max_val:.1f}s", font, DARK_GRAY,
              pygame.Rect(plot_x0 + plot_w - 60, plot_y0 - 10, 60, 20), "topright")
    draw_text(surface, "0s", font, DARK_GRAY,
              pygame.Rect(plot_x0 + plot_w - 60, plot_y0 + plot_h - 20, 60, 20), "topright")

def draw_stats_panel(surface, times, font_stats, font_list, page, delete_rects, edit_rects):
    stats_x, stats_y = 20, 100
    line_h = 26
    if not times:
        draw_text(surface, "无数据", font_stats, DARK_GRAY, pygame.Rect(stats_x, stats_y, 200, line_h), "topleft")
        return

    count = len(times)
    values = [rec['value'] for rec in times]
    avg = sum(values) / count
    fastest = min(values)
    slowest = max(values)
    last = times[-1]['value'] if times else 0
    stats = [
        f"次数: {count}",
        f"平均: {avg:.2f}s",
        f"最快: {fastest:.2f}s",
        f"最慢: {slowest:.2f}s",
        f"上次: {last:.2f}s",
    ]
    for i, text in enumerate(stats):
        draw_text(surface, text, font_stats, BLACK, pygame.Rect(stats_x, stats_y + i*line_h, 200, line_h), "topleft")

    stats_height = len(stats) * line_h

    chart_x = stats_x + 210
    chart_y = stats_y
    chart_w = WINDOW_WIDTH - chart_x - 20
    chart_h = stats_height
    chart_rect = pygame.Rect(chart_x, chart_y, chart_w, chart_h)
    draw_chart(surface, font_list, times, chart_rect)

    list_y = stats_y + stats_height + 20
    list_x = 20
    list_w = WINDOW_WIDTH - 40
    list_h = WINDOW_HEIGHT - list_y - 40
    pygame.draw.rect(surface, GRAY, (list_x, list_y, list_w, list_h), 1)

    total_pages = max(1, (count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0

    title = f"历史记录 (共{count}条，第{page+1}/{total_pages}页)   ← → 翻页"
    draw_text(surface, title, font_stats, DARK_GRAY, pygame.Rect(list_x+5, list_y+2, list_w-10, 22), "topleft")

    items = [(i, times[i]) for i in range(count-1, -1, -1)]
    start = page * ITEMS_PER_PAGE
    end = min(start + ITEMS_PER_PAGE, count)
    page_items = items[start:end]

    row_h = 28
    gap = 2
    row_y = list_y + 26
    max_rows = (list_h - 26) // (row_h + gap)
    display_items = page_items[:max_rows]

    delete_rects.clear()
    edit_rects.clear()

    for i, (orig_idx, rec) in enumerate(display_items):
        row_rect = pygame.Rect(list_x+2, row_y + i*(row_h+gap), list_w-4, row_h)
        pygame.draw.rect(surface, LIGHT_GRAY, row_rect)
        time_str = rec.get('time', '')
        value = rec['value']
        if time_str == '--' or not time_str:
            display_text = f"旧数据   {value:.2f}s"
        else:
            display_text = f"{time_str}   {value:.2f}s"
        draw_text(surface, display_text, font_list, BLACK,
                  pygame.Rect(row_rect.x+8, row_rect.y, row_rect.width-110, row_h), "topleft")  # 留空间给按钮

        # 修改按钮（蓝色，左侧）
        edit_rect = pygame.Rect(row_rect.right - 100, row_rect.y + 4, 40, row_h - 8)
        pygame.draw.rect(surface, EDIT_COLOR, edit_rect)
        draw_text(surface, "修改", font_list, WHITE, edit_rect, "center")
        edit_rects.append((edit_rect, orig_idx))

        # 删除按钮（红色，右侧）
        del_rect = pygame.Rect(row_rect.right - 50, row_rect.y + 4, 40, row_h - 8)
        pygame.draw.rect(surface, DELETE_COLOR, del_rect)
        draw_text(surface, "删除", font_list, WHITE, del_rect, "center")
        delete_rects.append((del_rect, orig_idx))

def draw_edit_dialog(surface, font, edit_text, cursor_visible, confirm_rect, cancel_rect):
    """绘制编辑对话框，返回确认和取消按钮矩形"""
    # 半透明遮罩
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    surface.blit(overlay, (0, 0))

    # 对话框主体
    dialog_w, dialog_h = 400, 200
    dialog_x = (WINDOW_WIDTH - dialog_w) // 2
    dialog_y = (WINDOW_HEIGHT - dialog_h) // 2
    pygame.draw.rect(surface, DIALOG_BG, (dialog_x, dialog_y, dialog_w, dialog_h))
    pygame.draw.rect(surface, BLACK, (dialog_x, dialog_y, dialog_w, dialog_h), 2)

    # 提示文字
    prompt = "请输入新的用时（秒）："
    draw_text(surface, prompt, font, BLACK, pygame.Rect(dialog_x+20, dialog_y+20, dialog_w-40, 30), "topleft")

    # 输入框
    input_rect = pygame.Rect(dialog_x+50, dialog_y+70, dialog_w-100, 40)
    pygame.draw.rect(surface, WHITE, input_rect)
    pygame.draw.rect(surface, BLACK, input_rect, 1)
    # 显示文本，并加上光标闪烁
    text_surf = font.render(edit_text, True, BLACK)
    text_rect = text_surf.get_rect(midleft=(input_rect.x+5, input_rect.centery))
    surface.blit(text_surf, text_rect)
    if cursor_visible:
        cursor_x = text_rect.right + 2
        pygame.draw.line(surface, BLACK, (cursor_x, input_rect.y+5), (cursor_x, input_rect.bottom-5), 2)

    # 确认按钮
    confirm_rect = pygame.Rect(dialog_x+80, dialog_y+140, 80, 35)
    pygame.draw.rect(surface, GREEN, confirm_rect)
    draw_text(surface, "确认", font, WHITE, confirm_rect, "center")

    # 取消按钮
    cancel_rect = pygame.Rect(dialog_x+240, dialog_y+140, 80, 35)
    pygame.draw.rect(surface, DELETE_COLOR, cancel_rect)
    draw_text(surface, "取消", font, WHITE, cancel_rect, "center")

    return confirm_rect, cancel_rect

# ===== 主程序 =====
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("魔方复原计时器")
    clock = pygame.time.Clock()

    font_title = get_chinese_font(28)
    font_time = get_chinese_font(100)
    font_mid = get_chinese_font(32)
    font_small = get_chinese_font(20)
    font_tiny = get_chinese_font(16)

    times = load_data()

    state = "idle"
    start_time = 0
    elapsed = 0.0
    last_record = None
    space_press_time = None
    page = "home"
    list_page = 0
    delete_rects = []
    edit_rects = []

    # 编辑对话框相关
    editing_index = None   # 正在编辑的记录索引，None表示无
    edit_text = ""         # 当前输入框内容
    cursor_visible = True
    cursor_timer = 0
    edit_confirm_rect = None
    edit_cancel_rect = None

    while True:
        # 光标闪烁
        cursor_timer += 1
        if cursor_timer >= 30:
            cursor_timer = 0
            cursor_visible = not cursor_visible

        # ===== 事件处理 =====
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            # 如果编辑对话框打开，只处理键盘输入和对话框按钮点击
            if editing_index is not None:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        # 确认修改
                        try:
                            new_val = float(edit_text)
                            if new_val >= 0:
                                times[editing_index]['value'] = new_val
                                save_data(times)
                                # 刷新列表（保持在当前页）
                                # 如果有必要，调整页码
                                total_pages = max(1, (len(times) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
                                if list_page >= total_pages:
                                    list_page = total_pages - 1
                                if list_page < 0:
                                    list_page = 0
                            else:
                                # 无效输入，忽略
                                pass
                        except ValueError:
                            pass
                        editing_index = None
                        edit_text = ""
                    elif event.key == pygame.K_ESCAPE:
                        editing_index = None
                        edit_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        edit_text = edit_text[:-1]
                    else:
                        # 只允许数字和小数点
                        if event.unicode and (event.unicode.isdigit() or event.unicode == '.'):
                            # 避免多个小数点
                            if event.unicode == '.' and '.' in edit_text:
                                pass
                            else:
                                edit_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    if edit_confirm_rect and edit_confirm_rect.collidepoint(pos):
                        # 确认
                        try:
                            new_val = float(edit_text)
                            if new_val >= 0:
                                times[editing_index]['value'] = new_val
                                save_data(times)
                                total_pages = max(1, (len(times) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
                                if list_page >= total_pages:
                                    list_page = total_pages - 1
                                if list_page < 0:
                                    list_page = 0
                            else:
                                pass
                        except ValueError:
                            pass
                        editing_index = None
                        edit_text = ""
                    elif edit_cancel_rect and edit_cancel_rect.collidepoint(pos):
                        editing_index = None
                        edit_text = ""
                # 跳过其他事件处理
                continue

            # 主界面事件处理（编辑对话框未打开时）
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    page = "stats" if page == "home" else "home"
                    list_page = 0
                    delete_rects.clear()
                    edit_rects.clear()

                if page == "stats":
                    if event.key == pygame.K_LEFT:
                        if list_page > 0:
                            list_page -= 1
                    elif event.key == pygame.K_RIGHT:
                        total_pages = max(1, (len(times) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
                        if list_page < total_pages - 1:
                            list_page += 1

                if state == "idle":
                    if event.key == pygame.K_SPACE:
                        space_press_time = pygame.time.get_ticks()
                elif state == "running":
                    elapsed = (pygame.time.get_ticks() - start_time) / 1000.0
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    new_record = {"time": now_str, "value": elapsed}
                    times.append(new_record)
                    save_data(times)
                    last_record = elapsed
                    state = "idle"
                    space_press_time = None
                    if page == "stats":
                        list_page = 0

            elif event.type == pygame.KEYUP:
                if state == "idle":
                    if event.key == pygame.K_SPACE and space_press_time is not None:
                        hold_time = pygame.time.get_ticks() - space_press_time
                        if hold_time >= HOLD_THRESHOLD:
                            start_time = pygame.time.get_ticks()
                            elapsed = 0.0
                            state = "running"
                            last_record = None
                        space_press_time = None

            elif event.type == pygame.MOUSEBUTTONDOWN and page == "stats":
                pos = event.pos
                # 先检测修改按钮
                for rect, idx in edit_rects:
                    if rect.collidepoint(pos):
                        # 打开编辑对话框
                        editing_index = idx
                        edit_text = f"{times[idx]['value']:.2f}"  # 当前值作为初始
                        # 重置光标
                        cursor_visible = True
                        cursor_timer = 0
                        break
                else:
                    # 检测删除按钮
                    for rect, idx in delete_rects:
                        if rect.collidepoint(pos):
                            if 0 <= idx < len(times):
                                del times[idx]
                                save_data(times)
                                total_pages = max(1, (len(times) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
                                if list_page >= total_pages:
                                    list_page = total_pages - 1
                                if list_page < 0:
                                    list_page = 0
                                delete_rects.clear()
                                edit_rects.clear()
                            break

        # 计时更新
        if state == "running":
            elapsed = (pygame.time.get_ticks() - start_time) / 1000.0

        # ===== 绘制 =====
        screen.fill(WHITE)

        if page == "home":
            draw_text(screen, "魔方复原计时器 (3阶)", font_title, DARK_GRAY,
                      pygame.Rect(20, 10, 300, 40), "topleft")

            time_text = f"{elapsed:.2f}s" if state == "running" else (
                f"{last_record:.2f}s" if last_record is not None else "0.00s"
            )
            draw_text(screen, time_text, font_time, BLUE if state == "running" else BLACK,
                      pygame.Rect(0, 130, WINDOW_WIDTH, 140), "center")

            if state == "idle":
                status = f"上次用时如上   (长按空格开始)" if last_record is not None else "长按空格键开始计时"
            else:
                status = "按任意键停止计时"
            draw_text(screen, status, font_mid, DARK_GRAY,
                      pygame.Rect(0, 290, WINDOW_WIDTH, 40), "center")

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            draw_text(screen, f"当前时间: {now_str}", font_small, DARK_GRAY,
                      pygame.Rect(WINDOW_WIDTH-200, WINDOW_HEIGHT-70, 190, 30), "topright")

            help_text = "空格：长按开始 | 任意键：停止 | S键：切换统计页"
            draw_text(screen, help_text, font_small, DARK_GRAY,
                      pygame.Rect(10, WINDOW_HEIGHT-30, WINDOW_WIDTH-20, 20), "center")

        else:  # stats 页
            draw_text(screen, "统计信息 (按 S 返回首页)", font_title, BLACK,
                      pygame.Rect(0, 10, WINDOW_WIDTH, 40), "center")

            if state == "running":
                status_info = f"计时中: {elapsed:.2f}s"
            else:
                status_info = "空闲"
            draw_text(screen, status_info, font_small, DARK_GRAY,
                      pygame.Rect(WINDOW_WIDTH-200, 10, 180, 30), "topright")

            draw_stats_panel(screen, times, font_small, font_tiny, list_page, delete_rects, edit_rects)

            draw_text(screen, "S键返回  |  ← → 翻页  |  点击“修改”编辑用时  |  点击“删除”移除记录",
                      font_small, DARK_GRAY,
                      pygame.Rect(10, WINDOW_HEIGHT-30, WINDOW_WIDTH-20, 20), "center")

        # 如果编辑对话框打开，绘制在最上层
        if editing_index is not None:
            confirm_rect, cancel_rect = draw_edit_dialog(screen, font_mid, edit_text, cursor_visible, edit_confirm_rect, edit_cancel_rect)
            edit_confirm_rect = confirm_rect
            edit_cancel_rect = cancel_rect

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()