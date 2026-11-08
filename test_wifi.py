import subprocess
import time

serial = "9889db393438353953"
ssid = "Limia Media"
pwd = "123123123"

# Pipe lệnh vào su
connect_cmd = f"cmd -w wifi connect-network '{ssid}' wpa2 {pwd}\n"
p = subprocess.Popen(["adb", "-s", serial, "shell", "su"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
stdout, stderr = p.communicate(input=connect_cmd)
print("STDOUT:", stdout.strip())

# Chờ 4s rồi kiểm tra trạng thái
time.sleep(4)
res = subprocess.run(["adb", "-s", serial, "shell", "dumpsys wifi | grep mWifiInfo"], capture_output=True, text=True).stdout
print("Wifi info:", res.strip())

# Ping thử
ping_res = subprocess.run(["adb", "-s", serial, "shell", "ping -c 1 -W 2 8.8.8.8"], capture_output=True, text=True).stdout
print("Ping 8.8.8.8:", ping_res.strip())
