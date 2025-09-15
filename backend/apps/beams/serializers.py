from rest_framework import serializers

ALLOWED_STIRRUP_DIA = {10, 12, 16}
ALLOWED_MAIN_DIA = {16, 20, 25, 28, 32, 36}

class BeamInputSerializer(serializers.Serializer):
    # I. Geometry (mm)
    width = serializers.FloatField(min_value=200, required=True)
    height = serializers.FloatField(min_value=200, required=True)
    cover = serializers.FloatField(min_value=25, required=True)

    # II. Concrete (MPa)
    fc = serializers.FloatField(min_value=17.0, required=True)
    agg_size = serializers.FloatField(min_value=0.0, required=False, allow_null=True)

    # III. Steel
    stirrup_dia = serializers.IntegerField(required=True)
    tension_bar_dia = serializers.IntegerField(required=True)
    compression_bar_dia = serializers.IntegerField(required=False, allow_null=True)

    n_tension = serializers.IntegerField(min_value=2, required=True)
    n_compression = serializers.IntegerField(min_value=0, required=False, default=0)

    fy_main = serializers.FloatField(min_value=275.0, required=True)  # MPa
    fy_stirrup = serializers.FloatField(min_value=1.0, required=True) # MPa (>0)

    # IV. Factored loads
    Mu = serializers.FloatField(min_value=0.0, required=True)  # kN-m
    Vu = serializers.FloatField(min_value=0.0, required=False, allow_null=True)  # kN

    lightweight = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        errors = {}

        # Stirrup diameter allowed list
        if data.get("stirrup_dia") not in ALLOWED_STIRRUP_DIA:
            errors["stirrup_dia"] = f"stirrup_dia must be one of {sorted(ALLOWED_STIRRUP_DIA)} mm"

        # Main bar diameters allowed list
        if data.get("tension_bar_dia") not in ALLOWED_MAIN_DIA:
            errors["tension_bar_dia"] = f"tension_bar_dia must be one of {sorted(ALLOWED_MAIN_DIA)} mm"
        cbd = data.get("compression_bar_dia")
        if cbd is not None and cbd not in ALLOWED_MAIN_DIA:
            errors["compression_bar_dia"] = f"compression_bar_dia must be one of {sorted(ALLOWED_MAIN_DIA)} mm or omitted"

        # Reasonable maximums (soft caps to catch typos)
        if data.get("width", 0) > 2000:
            errors["width"] = "width seems too large (>2000 mm)"
        if data.get("height", 0) > 3000:
            errors["height"] = "height seems too large (>3000 mm)"
        if data.get("cover", 0) > 100:
            errors["cover"] = "cover seems too large (>100 mm). Typical beam cover ~ 40 mm"
        if data.get("fc", 0) > 70:
            errors["fc"] = "f'c above 70 MPa is atypical for NSCP 2015 practical designs"
        if data.get("fy_main", 0) > 700:
            errors["fy_main"] = "Main bar yield strength seems high (>700 MPa)."
        if data.get("fy_stirrup", 0) > 700:
            errors["fy_stirrup"] = "Stirrup yield strength seems high (>700 MPa)."

        # If compression bars count is 0 then compression_bar_dia can be None
        if data.get("n_compression", 0) == 0 and data.get("compression_bar_dia") is None:
            pass
        elif data.get("n_compression", 0) > 0 and data.get("compression_bar_dia") is None:
            errors["compression_bar_dia"] = "Provide compression_bar_dia if n_compression > 0"

        # Forces
        if data.get("Vu") is None:
            data["Vu"] = 0.0
        if data.get("Mu") is None:
            data["Mu"] = 0.0

        if errors:
            raise serializers.ValidationError(errors)
        return data