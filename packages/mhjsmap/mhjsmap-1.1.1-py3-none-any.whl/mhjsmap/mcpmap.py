import asyncio
from typing import Any
import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.models import InitializationOptions
import requests
import os
from typing import Tuple, Optional, List
from mcp.server.lowlevel import NotificationOptions

AMAP_API_KEY = "cdd032ce94e08f5238985ff082c37a14"
# 创建低层级服务器实例
server = Server("amap-route-planner")

def amap_geocode(api_key: str, address: str) -> Optional[Tuple[float, float]]:
    """
    高德地理编码API：将地点名称转换为精确经纬度（解决“地点不精确”）
    :param api_key: 高德Web服务API Key
    :param address: 地点名称（如“杭州市西湖景区”“北京市天安门广场”）
    :return: (经度, 纬度)，失败返回None
    """
    url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": api_key,
        "address": address,  # 待转换的地点名称
        "city": "杭州",          # 可选：指定城市（如“杭州”），减少歧义
        "output": "json"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] == "1" and len(data["geocodes"]) > 0:
            # 提取经纬度（注意：API返回格式是“纬度,经度”，需交换顺序）
            lng_lat = data["geocodes"][0]["location"].split(",")
            lng = float(lng_lat[0])  # 经度
            lat = float(lng_lat[1])  # 纬度
            print(f"地理编码成功：{address} → 经度{lng:.6f}, 纬度{lat:.6f}")
            return (lng, lat)
        else:
            print(f"地理编码失败：{data.get('info', '未知错误')}")
            return None
    except Exception as e:
        print(f"地理编码API调用错误：{str(e)}")
        return None


def amap_route_planning(
    api_key: str,
    origin: Tuple[float, float],  # (起点经度, 起点纬度)
    destination: Tuple[float, float],  # (终点经度, 终点纬度)
    route_type: str = "driving"  # 路线类型：driving(驾车)/walking(步行)/transit(公交)
) -> Optional[List[Tuple[float, float]]]:
    """
    修复版：高德路径规划API，适配所有路线类型的polyline提取
    """
    # 1. 映射路线类型到对应的API地址
    route_urls = {
        "driving": "https://restapi.amap.com/v3/direction/driving",
        "walking": "https://restapi.amap.com/v3/direction/walking",
        "transit": "https://restapi.amap.com/v3/direction/transit/integrated"
    }
    if route_type not in route_urls:
        print(f"不支持的路线类型：{route_type}，请选择 driving/walking/transit")
        return None

    # 2. 拼接请求参数（公交路线需额外指定城市，避免歧义）
    params = {
        "key": api_key,
        "origin": f"{origin[0]},{origin[1]}",
        "destination": f"{destination[0]},{destination[1]}",
        "output": "json",
        "extensions": "all"  # 必须为"all"，否则不返回polyline
    }
    # 公交路线需添加城市参数（默认用起点城市，避免跨城公交数据混乱）
    if route_type == "transit":
        params["city"] = "330100"  # 010=北京，可改为目标城市的adcode（如杭州=330100）
        params["cityd"] = params["city"]  # 终点城市与起点城市一致（跨城需手动修改）

    try:
        response = requests.get(route_urls[route_type], params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        # 3. 检查API返回是否成功
        if data["status"] != "1":
            print(f"路径规划API返回错误：{data.get('info', '未知错误')}（状态码：{data.get('infocode')}）")
            return None
        if "route" not in data or len(data["route"]["paths"]) == 0:
            print("路径规划API未返回路线数据，可能是起点/终点过近或无路线")
            return None

        path = data["route"]["paths"][0]
        polyline_list = []  # 存储所有段的polyline

        # 4. 按路线类型提取polyline（核心修复部分）
        if route_type == "driving":
            # 驾车：直接从path中获取polyline（整段路线）
            if "polyline" in path:
                polyline_list.append(path["polyline"])
            else:
                print("驾车路线未找到polyline字段")
                return None

        elif route_type == "walking":
            # 步行：从每一步（steps）中提取polyline，再合并
            if "steps" not in path:
                print("步行路线未找到steps字段")
                return None
            for step in path["steps"]:
                if "polyline" in step:
                    polyline_list.append(step["polyline"])
                else:
                    print(f"步行步骤{step.get('step_id')}未找到polyline")

        elif route_type == "transit":
            # 公交：从每段行程（transits→segments）中提取polyline，再合并
            if "transits" not in path:
                print("公交路线未找到transits字段（可能无公交数据）")
                return None
            for transit in path["transits"]:
                if "segments" not in transit:
                    continue
                for segment in transit["segments"]:
                    # 公交段的polyline可能在segment或step中
                    if "polyline" in segment:
                        polyline_list.append(segment["polyline"])
                    elif "steps" in segment:
                        for step in segment["steps"]:
                            if "polyline" in step:
                                polyline_list.append(step["polyline"])
                    else:
                        print("公交段未找到polyline字段")

        # 5. 合并所有polyline，转换为经纬度列表
        if not polyline_list:
            print("未提取到任何polyline数据，无法生成路线")
            return None
        # 合并所有polyline字符串（用分号分隔，避免重复点）
        full_polyline = ";".join(polyline_list).replace(";;", ";").strip(";")
        # 转换为(经度, 纬度)列表
        route_points = []
        for point_str in full_polyline.split(";"):
            if point_str.strip() and "," in point_str:
                lng, lat = point_str.split(",")
                try:
                    route_points.append((float(lng), float(lat)))
                except ValueError:
                    print(f"无效的经纬度：{point_str}（跳过）")

        if len(route_points) < 2:
            print("提取的路线点过少，无法绘制路线（至少需要2个点）")
            return None

        print(f"路径规划成功：{route_type}路线，共{len(route_points)}个途经点")
        return route_points

    except requests.exceptions.HTTPError as e:
        print(f"HTTP错误：{e}（可能是API Key无效或参数错误）")
        print(f"服务器响应：{response.text[:500]}")  # 打印错误详情，便于排查
        return None
    except Exception as e:
        print(f"路径规划API调用错误：{str(e)}（可能是JSON解析失败）")
        return None

def amap_draw_route_map(
    api_key: str,
    origin: Tuple[float, float],
    destination: Tuple[float, float],
    route_points: List[Tuple[float, float]],
    save_path: str = "./route_map.png",
    map_size: str = "10*10",
    route_color: str = "0xFF0000"  # 路线颜色（红色，格式0xRRGGBB）
) -> Optional[bytes]:
    """
    高德静态地图API：绘制带起点、终点和路线的地图
    :param route_points: 路线途经点列表（由路径规划API获取）
    :return: 保存成功返回True，失败返回False
    """
    base_url = "https://restapi.amap.com/v3/staticmap"
    
    # 1. 配置路线参数（paths）：将途经点转为API要求的格式（lng1,lat1;lng2,lat2;...）
    if len(route_points) <= 2:
        # 若本身只有2个点（起点+终点），直接使用，不抽样
        sampled_points = route_points
    else:
        # 抽样逻辑：起点 + 每隔20个点取1个 + 终点
        sampled_points = [route_points[0]]  # 强制保留起点
        sampled_points.extend(route_points[1:-1:1])  # [1:-1] 排除起点和终点，避免重复
        if sampled_points[-1] != route_points[-1]:
            sampled_points.append(route_points[-1])

    # 将sampled_points转换为字符串格式 lng1,lat1;lng2,lat2;...
    route_polyline = ";".join([f"{lng},{lat}" for lng, lat in sampled_points])
    paths_param = f"3,0x0000ff,1,,:{route_polyline}"  # 10=线宽，0.8=透明度
    # 2. 配置起点/终点标注（markers）：起点绿色，终点红色，带文字标识
    markers_param = (
        f"mid,0x008000,S:{origin[0]},{origin[1]}|"
        f"mid,0xFF0000,E:{destination[0]},{destination[1]}"
    )
    
    # 3. 拼接请求参数
    params = {
        "key": api_key,
        "size": map_size,
        "scale": 2,  # 高清模式（图片更清晰）
        "paths": paths_param,  # 路线
        "markers": markers_param,  # 起点/终点标注
        "zoom": 12,  # 地图缩放级别（12级：兼顾路线范围和细节）
        "traffic": 0  # 不显示实时路况（0=不显示，1=显示）
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        
        # 验证返回内容是否为图片
        if "image" not in response.headers.get("Content-Type", ""):
            print(f"静态地图API返回非图片内容：{response.text[:300]}")
            return None
        
        # 直接返回图片二进制数据
        return response.content
    except Exception as e:
        print(f"静态地图API调用错误：{str(e)}")
        return None

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """列出可用的路线规划工具"""
    return [
        types.Tool(
            name="draw_route",
            description="绘制两个地点之间的路线地图",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_address": {"type": "string", "description": "起点地址"},
                    "end_address": {"type": "string", "description": "终点地址"},
                    "route_type": {
                        "type": "string", 
                        "description": "路线类型：driving(驾车)/walking(步行)/transit(公交)",
                        "default": "walking"
                    }
                },
                "required": ["start_address", "end_address"],
            }
        ),
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    """处理工具调用"""
    if name == "draw_route":
        # 在这里调用你的同步函数
        start_address = arguments["start_address"]
        end_address = arguments["end_address"]
        route_type = arguments.get("route_type", "walking")
        
        # 调用你原有的同步函数
        #origin = amap_geocode(AMAP_API_KEY, start_address)
        #destination = amap_geocode(AMAP_API_KEY, end_address)
        #route_points = amap_route_planning(AMAP_API_KEY, origin, destination, route_type)

        origin = await asyncio.to_thread(amap_geocode, AMAP_API_KEY, start_address)
        destination = await asyncio.to_thread(amap_geocode, AMAP_API_KEY, end_address)
        route_points = await asyncio.to_thread(amap_route_planning, AMAP_API_KEY, origin, destination, route_type)
        
        #image_data = await asyncio.to_thread(
        #        amap_draw_route_map, 
        #        AMAP_API_KEY, 
        #        origin, 
        #        destination, 
        #        route_points
        #   )
            
        #if not image_data:
        #    return {"success": False, "error": "地图生成失败"}
        
        #import base64
        #image_base64 = base64.b64encode(image_data).decode('utf-8')
        # 返回结构化数据
        #image_base64=""
        return {
            "success": True,
            "start_address": start_address,
            "end_address": end_address, 
            "route_type": route_type,
            "points_count": len(route_points) if route_points else 0,
            "version": "1.1.1",
            #"image_data": image_base64,
            "message": "路线规划成功"
        }
    else:
        raise ValueError(f"未知工具: {name}")

async def run():
    """运行服务器"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="amap-route-planner",
                server_version="1.1.1",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(run())
