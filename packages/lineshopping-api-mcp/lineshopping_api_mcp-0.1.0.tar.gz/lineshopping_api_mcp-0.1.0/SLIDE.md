- Agenda
  - ส่วนหนึ่งของ protocol ที่สำคัญมาพูดเท่านั้น
  - Sell ว่าฟังจนจบ จะสอนการทำ MCP server ใน 10 นาที
- What is MCP
- Local vs remote MCP
  - show ข้อดีข้อเสียของ stdio กับ streamable http
- MCP Primitive


- General MCP Architecture
- USB C Analogy
- Analogy for developer (GRPC, HTTP, GraphQL)
- How to implement MCP server
   Show the protocol in plain text to scare them and tell kidding,
- Good news you don't need to understand the real protocol
- Each language has their own SDK and library to use
-
- LINE Shopping introduction
- LINE Shopping API
- 30 lines of code with FastMCP















ผมจะขึ้นพูดในเวที LINE Developer conference หัวข้อเรื่อง
No rest no stress, connect MCP with LINE Shopping
โดยผู้เข้าฟังหลักๆก็จะเป็น Developer มาจากบริษัทอื่นๆประมาณ 1000 คน

จะพูดประมาณ 20 นาที โดยเนื้อหาที่ผมอยากจะพูดมีประมาณนี้

หลักๆคือ ผมอยากมาเล่าว่า mcp คืออะไร ทำอะไรได้บ้าง มีกี่ประเภท อธิบาย architecture ทั่วไปของ MCP และก็โชว์วิธีการพัฒนา MCP server อย่างรวดเร็วโดยใช้ FastMCP ซึ่งมีฟีเจอร์ที่ช่วยให้ระบบที่มี openapi spec อยู่แล้วสามารถ import เข้า FastMCP แล้ว work เลย โดยผมจะใช้ LINE Shopping API เป็นตัวอย่าง (เพื่อให้เข้ากับงาน LINE Thailand conference) จากนั้นผมจะโชว์การ connect AI Agent เข้ากับ mcp LINE Shopping แล้วโชว์การใช้งาน ซึ่งจะมีการใช้งานแบบเบสิก เช่นถามว่า ให้ช่วย list order ในช่วงนี้ที่ยังไม่จ่ายเงิน ซึ่งเป็นเคสเบสิกที่จริงๆ UI ของ Line myshop ก็สามารถทำได้อยู่แล้ว ผมก็จะเล่าต่อว่าประโยชน์ที่แท้จริงของ MCP คือการที่พอมันให้ LLM มาเชื่อมต่อแล้ว มันสามารถ connect กับระบบอื่นๆได้อีกมาก เช่น ผมอาจจะ import product จาก Shoppee เข้ามาใน LINE MyShop ได้เลย (ถ้ามีข้ออื่นๆน่าสนใจ ข่วยคิดให้ด้วย) ผมก็อยากเล่าประโยชน์ของการที่ developer ควรจะสร้าง MCP Server ให้กับ service ของตัวเอง ตอนจบผมอยากโปรโมตให้


สิ่งที่อยากให้ช่วย
- ช่วยคิดประโยคเปิดโดนใจ โดยผมอยากจะให้เป็น structure แบบ problem-solution
- ช่วยคิดโครงสร้าง slide ที่ผมจะ present
- ช่วยคิดประโยคปิดโดนใจ โดยผมอยากจะเน้นให้ Developer ลองไปพัฒนา MCP Server สำหรับ service ตัวเองเพื่อเชื่อมต่อกับ LLM ได้ง่ายๆ

- What is MCP
- General MCP Architecture
- 30 lines of code with FastMCP อันนี้ผมจะโชว์โค้ดโดยใช้ lib FastMCP