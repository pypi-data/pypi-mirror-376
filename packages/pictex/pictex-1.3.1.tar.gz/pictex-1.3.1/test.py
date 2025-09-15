from pictex import *

(
    Canvas()
    .color("#ffffff72")
    .font_family("Impact")
    .font_size(150)
).render("hey").save("t.png")

# si uso to_pillow() el resultado es diferente que si no lo uso
# debería ser igual, dado que debería mantenerse la misma imagen.