From outside nothing changes. Once the camera is inside the cube you only see the clear color: every face is now seen from behind, and all of them are culled. The live demo shows the reverse case when you choose `.front`.
---
Swap two of the three vertices of each triangle on that face. From outside that face is now clockwise, so it is treated as a back face and culled, leaving a hole through which you see the inside of the cube, which is culled as well.
---
This is the shader of the live demo above: take a `bool` parameter marked `[[front_facing]]` and choose the color from it. Flip the normal for back faces if you light them.
