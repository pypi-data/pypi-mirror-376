# src/vegasglow/runner.py
from typing import Optional, Sequence, Tuple

import numpy as np

from .sampler import MultiThreadEmcee
from .types import FitResult, ModelParams, ObsData, ParamDef, Scale, Setups, VegasMC


class Fitter:
    """
    High-level MCMC interface for fitting an afterglow model.
    """

    def __init__(
        self, data: ObsData, config: Setups, num_workers: Optional[int] = None
    ):
        """
        Parameters
        ----------
        data : ObsData
            Observed light curves and spectra.
        config : Setups
            Model configuration (grids, environment, etc).
        """
        self.data = data
        self.config = config
        self.num_workers = num_workers
        # placeholders to be set in fit()
        self._param_defs = None
        self._to_params = None

    def fit(
        self,
        param_defs: Sequence[ParamDef],
        resolution: Tuple[float, float, float] = (0.3, 1, 10),
        total_steps: int = 10_000,
        burn_frac: float = 0.3,
        thin: int = 1,
        top_k: int = 10,
    ) -> FitResult:
        """
        Run the MCMC sampler.

        Parameters
        ----------
        param_defs :
            A sequence of (name, init, lower, upper) for each free parameter.
        resolution :
            (t_grid, theta_grid, phi_grid) for the coarse MCMC stage.
        total_steps :
            Total number of MCMC steps.
        burn_frac :
            Fraction of steps to discard as burn-in.
        thin :
            Thinning factor for the returned chain.
        top_k :
            Number of top fits to save in the result.

        Returns
        -------
        FitResult
        """
        # 1) build lists for emcee
        defs = list(param_defs)
        self._param_defs = defs

        # build the emcee bounds & initials
        labels, inits, lowers, uppers = zip(
            *(
                (
                    pd.name,
                    (
                        0.5 * (np.log10(pd.lower) + np.log10(pd.upper))
                        if pd.scale is Scale.LOG
                        else 0.5 * (pd.lower + pd.upper)
                    ),
                    (np.log10(pd.lower) if pd.scale is Scale.LOG else pd.lower),
                    (np.log10(pd.upper) if pd.scale is Scale.LOG else pd.upper),
                )
                for pd in defs
                if pd.scale is not Scale.FIXED
            )
        )
        init = np.array(inits)
        pl = np.array(lowers)
        pu = np.array(uppers)

        # Validate that all parameter names are valid ModelParams attributes
        p_test = ModelParams()
        for pd in defs:
            try:
                getattr(p_test, pd.name)
            except AttributeError:
                raise AttributeError(f"'{pd.name}' is not a valid MCMC parameter")

        # 2) build a fast transformation closure
        def to_params(x: np.ndarray) -> ModelParams:
            p = ModelParams()
            i = 0
            for pd in defs:
                if pd.scale is Scale.FIXED:
                    # fixed param: always pd.init
                    setattr(p, pd.name, 0.5 * (pd.lower + pd.upper))
                else:
                    v = x[i]
                    if pd.scale is Scale.LOG:
                        real = 10**v
                    else:
                        real = v
                    setattr(p, pd.name, real)
                    i += 1
            return p

        self._to_params = to_params

        mcmc = MultiThreadEmcee(
            param_config=(labels, init, pl, pu),
            to_params=to_params,
            model_cls=VegasMC,
            num_workers=self.num_workers,
        )
        result: FitResult = mcmc.run(
            data=self.data,
            base_cfg=self.config,
            resolution=resolution,
            total_steps=total_steps,
            burn_frac=burn_frac,
            thin=thin,
            top_k=top_k,
        )
        return result

    def _with_resolution(self, resolution: Tuple[float, float, float]) -> Setups:
        """
        Clone self.config (without pickle) and override t/theta/phi grids.
        """
        cfg = type(self.config)()
        # copy all public attributes
        for attr in dir(self.config):
            if attr.startswith("_"):
                continue
            if hasattr(cfg, attr):
                try:
                    setattr(cfg, attr, getattr(self.config, attr))
                except Exception:
                    pass
        # override grids
        cfg.phi_resol, cfg.theta_resol, cfg.t_resol = resolution
        return cfg

    def specific_flux(
        self,
        best_params: np.ndarray,
        t: np.ndarray,
        nu: np.ndarray,
        resolution: Optional[Tuple[float, float, float]] = (0.3, 1, 10),
    ) -> np.ndarray:
        """
        Compute light curves at the best-fit parameters.

        Parameters
        ----------
        best_params : 1D numpy array
            The vector returned in FitResult.best_params.
        t : 1D numpy array
            Times at which to evaluate.
        nu : 1D numpy array
            Frequencies at which to evaluate.

        Returns
        -------
        array_like
            Shape (n_bands, t.size)
        """
        if self._to_params is None:
            raise RuntimeError("Call .fit(...) before .light_curves()")

        cfg_local = self._with_resolution(resolution)
        p = self._to_params(best_params)

        model = VegasMC(self.data)
        model.set(cfg_local)
        return model.specific_flux(p, t, nu)

    def flux(
        self,
        best_params: np.ndarray,
        t: np.ndarray,
        nu_min: float,
        nu_max: float,
        num_points: int,
        resolution: Optional[Tuple[float, float, float]] = (0.3, 1, 10),
    ) -> np.ndarray:
        """
        Compute light curves at the best-fit parameters.

        Parameters
        ----------
        best_params : 1D numpy array
            The vector returned in FitResult.best_params.
        t : 1D numpy array
            Times at which to evaluate.
        nu_min : float
            Minimum frequency at which to evaluate.
        nu_max : float
            Maximum frequency at which to evaluate.
        num_points : int
            Number of points to sample between nu_min and nu_max.

        Returns
        -------
        array_like
            Shape (n_bands, t.size)
        """

        if self._to_params is None:
            raise RuntimeError("Call .fit(...) before .light_curves()")

        cfg_local = self._with_resolution(resolution)
        p = self._to_params(best_params)

        model = VegasMC(self.data)
        model.set(cfg_local)
        return model.flux(p, t, nu_min, nu_max, num_points)
