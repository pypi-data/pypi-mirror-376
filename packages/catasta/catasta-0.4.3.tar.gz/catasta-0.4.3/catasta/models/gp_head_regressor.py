import torch
from torch import Tensor, Size
from torch.nn import Module

from gpytorch.models import ApproximateGP
from gpytorch.variational import (
    CholeskyVariationalDistribution,
    VariationalStrategy,
    IndependentMultitaskVariationalStrategy,
)
from gpytorch.means import ZeroMean, ConstantMean, Mean
from gpytorch.kernels import (
    Kernel,
    ScaleKernel,
    RBFKernel,
    MaternKernel,
    RQKernel,
    RFFKernel,
    PeriodicKernel,
    LinearKernel,
)
from gpytorch.distributions import MultivariateNormal
from gpytorch.likelihoods import (
    Likelihood,
    GaussianLikelihood,
    BernoulliLikelihood,
    LaplaceLikelihood,
    SoftmaxLikelihood,
    StudentTLikelihood,
    BetaLikelihood,
    MultitaskGaussianLikelihood,
)


def _get_kernel(id: str, n_inputs: int, use_ard: bool, batch_shape: Size) -> Kernel:
    ard_num_dims = n_inputs if use_ard else None
    id = id.lower()
    if id == "rq":
        return RQKernel(ard_num_dims=ard_num_dims, batch_shape=batch_shape)
    if id == "matern":
        return MaternKernel(ard_num_dims=ard_num_dims, batch_shape=batch_shape)
    if id == "rbf":
        return RBFKernel(ard_num_dims=ard_num_dims, batch_shape=batch_shape)
    if id == "rff":
        return RFFKernel(num_samples=n_inputs, batch_shape=batch_shape)
    if id == "periodic":
        return PeriodicKernel(ard_num_dims=ard_num_dims, batch_shape=batch_shape)
    if id == "linear":
        return LinearKernel(ard_num_dims=ard_num_dims, batch_shape=batch_shape)
    raise ValueError(f"Unknown kernel: {id}")


def _get_mean_module(id: str, batch_shape: Size) -> Mean:
    id = id.lower()
    if id == "constant":
        return ConstantMean(batch_shape=batch_shape)
    if id == "zero":
        return ZeroMean(batch_shape=batch_shape)
    raise ValueError(f"Unknown mean: {id}")


def _get_likelihood(id: str, n_outputs: int) -> Likelihood:
    if n_outputs > 1:
        return MultitaskGaussianLikelihood(num_tasks=n_outputs)
    id = id.lower()
    if id == "gaussian":
        return GaussianLikelihood()
    if id == "bernoulli":
        return BernoulliLikelihood()
    if id == "laplace":
        return LaplaceLikelihood()
    if id == "softmax":
        return SoftmaxLikelihood()
    if id == "studentt":
        return StudentTLikelihood()
    if id == "beta":
        return BetaLikelihood()
    raise ValueError(f"Unknown likelihood: {id}")


class GPHeadRegressor(ApproximateGP):
    def __init__(
        self,
        *,
        pre_model: Module,
        pre_model_output_dim: int,
        n_inputs: int,
        n_outputs: int,
        n_inducing_points: int,
        kernel: str = "rq",
        mean: str = "constant",
        likelihood: str = "gaussian",
        use_ard: bool = True,
    ) -> None:
        self._n_outputs = n_outputs

        batch_shape = Size([])
        inducing_points = torch.randn(n_inducing_points, n_inputs, dtype=torch.float32)

        variational_distribution = CholeskyVariationalDistribution(
            n_inducing_points,
            batch_shape=batch_shape,
        )
        base_variational_strategy = VariationalStrategy(
            self,
            inducing_points,
            variational_distribution,
            learn_inducing_locations=True,
        )
        variational_strategy = (
            base_variational_strategy
            if n_outputs == 1
            else IndependentMultitaskVariationalStrategy(
                base_variational_strategy=base_variational_strategy,
                num_tasks=n_outputs,
            )
        )

        super().__init__(variational_strategy)
        self.mean_module = _get_mean_module(mean, batch_shape)
        self.covar_module = ScaleKernel(
            _get_kernel(kernel, pre_model_output_dim, use_ard, batch_shape),
            batch_shape=batch_shape,
        )
        self.likelihood = _get_likelihood(likelihood, n_outputs)
        self.pre_model = pre_model

    def forward(self, x: Tensor) -> MultivariateNormal:
        x = self.pre_model(x)
        if x.dim() > 2:
            x = x.view(x.shape[0], -1)
        mean_x = self.mean_module(x)
        covar_x = self.covar_module(x)

        return MultivariateNormal(mean_x, covar_x) # type: ignore
