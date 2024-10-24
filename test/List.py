import csv

def process_csv_file(filepath="1.csv"):
    """
    读取一个CSV文件，处理'dw'和'id'列。如果'dw'列非空，则'id'列的值保持为上一行的'id'值；如果'dw'列为空，则'id'列的值加1。

    Args:
        filepath: CSV文件的路径。默认为"1.csv"。

    Returns:
        一个字典列表，每个字典代表一行处理后的数据，包含'id'和'dw'列。
        如果文件不存在或处理过程中出现错误，则返回None。
    """
    try:
        with open(filepath, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            data = []
            previous_id = None  # 初始化previous_id为None，用于处理第一行
            previous_row = None # Keep track of the previous row

            for row in reader:
                try:
                    dw = row['dw']
                    current_id = int(row['id']) if row['id'] else None # Handle potential empty 'id'

                    if previous_id is None: # First row
                        previous_id = current_id
                    elif dw: # If 'dw' is not empty, keep the same ID
                        current_id = previous_id
                    else: # If 'dw' is empty, increment ID
                        current_id = previous_id + 1

                    data.append({'id': current_id, 'dw': dw})
                    previous_id = current_id # Update previous_id for the next iteration
                except (ValueError, KeyError) as e:
                    print(f"处理行 {row} 时出错: {e}")
                    return None

            return data

    except FileNotFoundError:
        print(f"错误: 文件'{filepath}' 未找到。")
        return None


# 示例用法:
result = process_csv_file()

if result:
    for row in result:
        print(row)

    # 将处理后的数据写入新的CSV文件
    with open('output.csv', 'w', newline='', encoding='utf-8') as outfile:
        fieldnames = ['id', 'dw']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(result)
else:
    print("CSV文件处理失败。")