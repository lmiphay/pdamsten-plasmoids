plasmoid.setAspectRatioMode(IgnoreAspectRatio);
layout = new LinearLayout(plasmoid);
label = new Label();
layout.addItem(label);

plasmoid.configChanged = function()
{
    label.text = plasmoid.readConfig("text");
}

plasmoid.configChanged();


