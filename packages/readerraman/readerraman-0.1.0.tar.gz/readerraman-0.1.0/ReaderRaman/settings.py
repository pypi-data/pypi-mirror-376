from json import load
from pydantic import BaseModel, Field


class Settings(BaseModel):
    laser_power: int = Field(..., alias="Laser Power (mW)")
    rep_rate_kHz: int = Field(..., alias="Rep Rate (kHz)")
    pulse_width_ns: int = Field(..., alias="Pulse width (ns)")
    amplifier_Power: int = Field(..., alias="Amplifier Power")
    number_of_averages: int = Field(..., alias="Number of Averages")
    sample_frequency: int = Field(..., alias="Sample Frequency")
    fiber_length_m: int = Field(..., alias="Fiber Length")
    calibration_fiber_length_m: int = Field(..., alias="Calibration Fiber Length")
    refractive_index: float = Field(..., alias="Refractive Index")
    fiber_end_offset: int = Field(..., alias="Fiber end offset")
    moving_average_samples: int = Field(..., alias="Moving Average Samples")
    alpha_coeff: float = Field(..., alias="Alpha coeff")
    coefficients: list[float] = Field(..., alias="Coefficients")
    note: str = Field(..., alias="Note")
    APD: list[dict] = Field(..., alias="APD")

    class Config:
        validate_by_name = True
        allow_population_by_alias = True


def parseSettingsDict(settings_dict: dict) -> Settings:
    settings_dict.pop("Time Stamp", None)
    return Settings.model_validate(settings_dict)


if __name__ == "__main__":
    # filename='data/2021/profiles/2021-11-08_16-51-16.652_rawarray.json'
    filename = "data/2025-09-11_10-10-21,202_CohDTS_50ns_480Kavg_25C.json"
    # filename='C:/Users/marbr/OneDrive/Cohaerentia/00 - Sensori/Brillouin/BOTDA/Misure/2023_12 - polyfit/gialla_15MHz/rawarray/2023-12-11_10-30-23.093_rawarray.json'
    with open(filename) as file:
        text = load(file)
    setting_test = text["Parameters"]
    settings = parseSettingsDict(setting_test)
    print(settings)
