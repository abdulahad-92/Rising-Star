from matplotlib import pyplot as plt
import base64
from io import BytesIO

# Example: Create a simple plot
plt.plot([1, 2, 3], [4, 5, 6])
plt.title("Sample Plot")
buf = BytesIO()
plt.savefig(buf, format='png')
radar_chart_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
plt.close()