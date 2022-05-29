from ..defaults import *
from ..activations import *
from ..conversions import toComplex
from .routing import KnowledgeCollider


# TODO: Fuck, this isn't needed, integrate functionality into the router; break out method
# TODO: FUCK, THIS IS NEEDED. FUCK THE ROUTER, IT ROUTES AND IS TYPE COMPATIBLE WITH IT'S FILTERS
class Aggregator(nn.Module):
    def __init__(self, lensSlots:int=AGGREGATE_LENSES, outputSamples:int=-1, 
    colliders:List[KnowledgeCollider]=None, selectorSide:int=SUPERSINGULAR_PRIMES_LH[3], cdtype:t.dtype=DEFAULT_COMPLEX_DTYPE):
        # Do not use the attentive resample option available in the aggregator as it is essentially 
        #   just a lensing system.
        super(Aggregator, self).__init__()

        # Used for building complex types
        typeDummy:t.Tensor = toComplex(t.zeros((1), dtype=cdtype))

        # Hold the amount of output samples to be used internally by the module in the nn module parameters
        self.outputSamples:nn.Parameter = nn.Parameter(t.tensor([outputSamples], dtype=t.int64), requires_grad=False)

        # Hold the amount of lenses used in the module in the nn module parameters
        self.lensSlots:nn.Parameter = nn.Parameter(t.tensor([lensSlots], dtype=t.int64), requires_grad=False)
        
        # Each lens to be interpolated between during the signal evaluation
        # The first lens is used for the input signal in a GREISS_SAMPLES size batch,
        #   the second lens is for the post filter evaluated patch also in a GREISS_SAMPLES size batch. 
        self.lensBasis:nn.Parameter = nn.Parameter(t.randn((2, lensSlots, GREISS_SAMPLES), dtype=typeDummy.dtype))
        
        # Because each signal is resignalled to be in to having GREISS_SAMPLES as a size,
        #   the lens selectors select the respective lenses by viewing the entirety and evaluating
        #   to a single value.
        self.lensSelectorProj:nn.Parameter = nn.Parameter(t.randn((2, GREISS_SAMPLES, selectorSide), dtype=typeDummy.dtype))
        # The final convolution needs to be real valued to properly interpolate the lenses
        self.lensSelectorConv:nn.Parameter = nn.Parameter(t.randn((2, selectorSide, 1), dtype=typeDummy.real.dtype))

        # The starting set of KnowledgeColliders to run the feeding signals through
        self.colliders:nn.ModuleList = nn.ModuleList(colliders)


    def __colliderCaster__(self, collider) -> KnowledgeCollider:
        # Type check
        assert collider is KnowledgeCollider
        
        # Cast-ish for linting and suggestions
        return collider


    def addCollider(self, collider:KnowledgeCollider):
        # Type and value check the arguments
        self.__colliderCaster__(collider)

        # Add the collider, duplicates will just increase the signal gain
        self.colliders.append(collider)


    def __keyToIdx__(self, collider:KnowledgeCollider) -> Tuple[t.Tensor]:
        # Running data for the method
        result:Tuple[t.Tensor] = (None, None)
        selectorSide = self.lensSelectorProj.size(-1)

        # Turn the key basis vector into something that can be maximally remapped through Greiss algebra
        greissKey:t.Tensor = tfft.ifft(itanh(collider.keyBasis), n=GREISS_SAMPLES, norm='ortho', dim=-1)

        # Matmul the Greiss key into the latent type used to select lenses
        # Use an irfft as an activation function to get to real values for the
        #   final convolution
        lensTriuSignal:t.Tensor = tfft.irfft(greissKey @ self.lensSelectorProj, n=selectorSide, norm='ortho', dim=-1)

        # Evaluate the final lens selection through a convolution and an activation,
        #   binding the value between (0.0, 1.0)
        ldx:t.Tensor = nnf.sigmoid(lensTriuSignal @ self.lensSelectorConv)


    def forward(self, a:t.Tensor, b:t.Tensor, callColliders:bool=False) -> Tuple[t.Tensor]:
        # Running data for caching the outputs of the internal colliders
        collCount = len(self.colliders)
        ldx = [None] * collCount    # Lens index -> Tuple([input, output])

        for idx, collModule in enumerate(self.colliders):
            # Do a light casting to a KnowledgeCollider
            collider:KnowledgeCollider = self.__colliderCaster__(collModule)

            # If requested, call the stored colliders
            if callColliders:
                _ = collider.forward(a, b)
            
            # Get the associated lens position for the collision
            ldx[idx] = self.__keyToIdx__(collider)
