from json import load, loads
import numpy as np
import numpy.typing as npt
import h5py
import plotly.graph_objects as go

from datetime import datetime, timezone
from os import path, PathLike, strerror
from glob import glob
from typing import Union, Literal, get_args
import errno
from progress.bar import Bar

from ReaderRaman.settings import Settings, parseSettingsDict


class NoFilesSelected(Exception):
    def __init__(self, folder, message="No file found in folder"):
        self.message = f"{message}: {folder}"
        super().__init__(self.message)


Data_Available = Literal["apd_1", "apd_2", "ratio", "temperature"]


class Single:

    filename: str = ""
    settings: Settings
    position_m: npt.ArrayLike
    apd_1: npt.ArrayLike
    apd_2: npt.ArrayLike
    ratio: np.ndarray = npt.ArrayLike
    reference_temperature_C: float
    temperature: datetime = datetime.now

    def __init__(self, filename: PathLike, name: str = None) -> None:
        """Load a single measure from a json file."""
        self.filename = filename
        with open(self.filename) as file:
            text = load(file)
        self.timestamp = datetime.strptime(
            text["Parameters"]["Time Stamp"], "%Y-%m-%d" + "T" + "%H:%M:%S.%f" + "Z"
        )  # 2025-09-11T08:10:21.202Z
        self.settings = parseSettingsDict(text["Parameters"])

        if not name:
            self.name = self.timestamp.strftime("%m/%d/%Y, %H:%M:%S")
        else:
            self.name = name

        self.position_m = np.array(text["Position"])
        self.apd_1 = np.array(text["APD1"])
        self.apd_2 = np.array(text["APD2"])
        self.ratio = np.array(text["Raman"])
        self.temperature = np.array(text["Temperature"])
        self.reference_temperature_C = text["Parameters"]["Coefficients"][0]

    def plot(
        self,
        to_plot: Data_Available = "temperature",
        title: str = None,
    ) -> go.Figure:

        fig = go.Figure(
            layout=dict(
                title=title if title else self.filename,
                yaxis_title=to_plot.capitalize(),
                xaxis_title="Position (m)",
            ),
            data=go.Scatter(
                x=self.position_m,
                y=getattr(self, to_plot),
                mode="lines",
                showlegend=False,
            ),
        )
        return fig


class Multiple:

    def __init__(
        self,
        folder: PathLike,
        n_measure: int = None,
        start_measure: Union[int, datetime] = 0,
        stop_measure: datetime = None,
    ):

        self.folder = folder

        filelist = glob(path.join(folder, "*.json"))
        if start_measure and isinstance(start_measure, datetime):
            timestamps_files = [
                datetime.strptime(
                    "_".join(path.basename(file).split("_")[:2]), "%Y-%m-%d_%H-%M-%S.%f"
                )
                for file in filelist
            ]
            primo = next(
                (
                    x
                    for x, value in enumerate(timestamps_files)
                    if value >= start_measure
                ),
                0,
            )
            if stop_measure:
                ultimo = next(
                    (
                        x
                        for x, value in enumerate(timestamps_files)
                        if value > stop_measure
                    ),
                    len(filelist),
                )
            elif n_measure:
                ultimo = primo + n_measure
            else:
                ultimo = len(filelist)
            filelist = filelist[primo:ultimo]

        if n_measure and (start_measure == 0 or isinstance(start_measure, int)):
            filelist = filelist[start_measure : start_measure + n_measure]

        if isinstance(start_measure, int) and not n_measure and stop_measure:
            timestamps_files = [
                datetime.strptime(
                    "_".join(path.basename(file).split("_")[:2]), "%Y-%m-%d_%H-%M-%S.%f"
                )
                for file in filelist
            ]
            ultimo = next(
                (x for x, value in enumerate(timestamps_files) if value > stop_measure),
                len(filelist),
            )
            filelist = filelist[start_measure:ultimo]

        if len(filelist) == 0:
            raise NoFilesSelected(folder=folder)

        timestamps = list()
        with Bar("Reading files", max=len(filelist)) as bar:
            for file in filelist:
                temp = Single(filename=file)
                timestamps.append(temp.timestamp)
                try:
                    self.apd_1 = np.vstack((self.apd_1, temp.apd_1))
                    self.apd_2 = np.vstack((self.apd_2, temp.apd_2))
                    self.ratio = np.vstack((self.ratio, temp.ratio))
                    self.temperature = np.vstack((self.temperature, temp.temperature))
                    self.reference_temperature_C.append(temp.reference_temperature_C)
                except AttributeError:
                    self.apd_1 = temp.apd_1
                    self.apd_2 = temp.apd_2
                    self.ratio = temp.ratio
                    self.temperature = temp.temperature
                    self.reference_temperature_C = [temp.reference_temperature_C]
                bar.next()

        self.timestamps = np.array(timestamps)
        self.settings = temp.settings
        self.position_m = temp.position_m
        self.reference_temperature_C = np.array(self.reference_temperature_C)

    @property
    def shape(self) -> list[int]:
        """Dimensioni del data caricato. (tempo, posizione)"""
        return np.shape(self.temperature)

    def filter_by_position(
        self,
        position_m: float,
        to_filter: Data_Available = "temperature",
    ) -> tuple[npt.ArrayLike, float, int]:
        """Restituisce il profilo in funzione del tempo in una posizione specifica."""
        if position_m < self.position_m[0] or position_m > self.position_m[-1]:
            raise ValueError

        position_index = np.abs(self.position_m - position_m).argmin()
        return (
            getattr(self, to_filter)[:, position_index],
            self.position_m[position_index],
            position_index,
        )

    def plot(
        self,
        to_plot: Data_Available = "temperature",
        title: str = None,
    ) -> go.Figure:

        fig = go.Figure(
            layout=dict(
                title=title if title else self.folder,
                yaxis_title=to_plot.capitalize(),
                xaxis_title="Position (m)",
            )
        )

        for i, time in enumerate(self.timestamps):
            fig.add_trace(
                go.Scatter(
                    x=self.position_m,
                    y=getattr(self, to_plot)[i, :],
                    mode="lines",
                    name=time.strftime("%m/%d/%Y, %H:%M:%S"),
                )
            )
        return fig

    def plot_positions_vs_time(
        self,
        positions_m: float | list[float],
        to_plot: Data_Available = "temperature",
        title: str = None,
    ) -> go.Figure:

        if not isinstance(positions_m, list):
            positions_m = [positions_m]

        fig = go.Figure(
            layout=dict(
                title=title if title else self.folder,
                showlegend=True,
                xaxis_title="Time",
                yaxis_title=to_plot.capitalize(),
                legend_title="Position (m)",
                hovermode="x unified",
            )
        )
        for position in sorted(positions_m):
            data, real_position, _ = self.filter_by_position(
                position_m=position, to_filter=to_plot
            )
            fig.add_trace(
                go.Scatter(x=self.timestamps, y=data, name=f"{real_position:.3f}")
            )
        return fig

    def export_to_h5(self, filename: PathLike) -> None:
        """
        Esporta il contenuto di un oggetto Multiple in un file HDF5.
        """
        with h5py.File(filename, "w", track_order=True) as f:

            f.attrs["folder"] = self.folder
            f.attrs["settings"] = self.settings.model_dump_json()
            f.attrs["first_measure_utc"] = self.timestamps[0].strftime(
                "%Y-%m-%d, %H:%M:%S.%f"
            )
            f.attrs["last_measure_utc"] = self.timestamps[-1].strftime(
                "%Y-%m-%d, %H:%M:%S.%f"
            )
            pos_set = f.create_dataset("position_m", data=self.position_m, dtype="f8")
            pos_set.make_scale("position (m)")

            temp_timestamps = [np.datetime64(i).astype("<i8") for i in self.timestamps]
            time_set = f.create_dataset(
                "timestamps",
                data=temp_timestamps,
                dtype="<i8",
                maxshape=(None,),
                compression="gzip",
            )
            time_set.dims[0].label = "UTC Epochtime (us)"

            for attr in get_args(Data_Available):
                f.create_dataset(
                    attr, data=getattr(self, attr), dtype="f4", compression="gzip"
                )


class MultipleH5(Multiple):

    def __init__(
        self,
        filename: PathLike,
    ):
        self.filename = filename

        if not path.isfile(filename):
            raise FileNotFoundError(errno.ENOENT, strerror(errno.ENOENT), filename)

        with h5py.File(filename, "r") as f:
            self.folder = f.attrs["folder"]

            self.position_m = f["position_m"][:]
            for attr in get_args(Data_Available):
                setattr(self, attr, np.squeeze(f[attr][:]))
            self.timestamps = [
                datetime.fromtimestamp(timestamp / 1000000)  # FIXME, timezone.utc)
                for timestamp in f["timestamps"][:]
            ]
            self.settings = parseSettingsDict(loads(f.attrs["settings"]))
