Give the outline state a normal depth test: `depthCompareFunction = .less` instead of `.always`. The enlarged copy is then hidden by anything closer to the camera. In the live demo, untick "ignore depth".
---
Use the stencil-writing state only while drawing the cube you want outlined, and draw the others with the ordinary depth state. Then draw the enlarged copy of that one cube only. The reference value could also select between objects: write 1 for one cube and 2 for another, and test against the value you want.
