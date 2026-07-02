import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material


Button {
    id: control

    property string type: "primary" 

    property string hoverAlphaHex: "1A"

    flat: true
    hoverEnabled: true

    function getColor(role) {
        if (role === "success") {
            return control.Material.color(control.Material.Green)
        } else if (role === "warning") {
            return control.Material.color(control.Material.Orange)
        } else if (role === "danger") {
            return control.Material.color(control.Material.Red)
        } else {
            return control.Material.color(control.Material.accent)
        }
    }

    Material.foreground: control.hovered
        ? control.getColor(control.type)
        : control.parent.Material.foreground

    Material.background: control.hovered
        ? ("#" + control.hoverAlphaHex + control.getColor(control.type).toString().substring(1))
        : "transparent"
}
