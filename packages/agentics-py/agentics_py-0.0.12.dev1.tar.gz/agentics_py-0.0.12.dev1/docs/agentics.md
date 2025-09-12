# Agentics

Agentics objects are wrappers around list of objects having the same Pydantic Type.
They are designed to enable async logical transduction among their instances.
Agentics enable us to think about AI workflows in terms of structured data transformations rather than agent behaviours, knowledge and tasks. 

## The Agentics class
Agentics is a Python class that wraps a list of Pydantic objects and enables structured, type-driven logical transduction between them.

Internally, Agentics is implemented as a Pydantic model. It holds:
	•	atype: a reference to the Pydantic class shared by all objects in the list.
	•	states: a list of Pydantic instances, each validated to be of type atype.
    •	tools: a list of tools (CrewAI or Langchain) to be used for transduction

```python
from typing import Type, List
from pydantic import BaseModel, Field

class Agentics(BaseModel):
    atype: Type[BaseModel] = Field(
        ..., 
        description="The shared Pydantic type for all elements in the list."
    )
    states: List[BaseModel] = []
    tools: Optional[List[Any]] = Field(
        None,
        description="List of tools to be used by the agent"
    )
    ...
```


## Atypes

Agentics types are dynamic as they can be modified at run time while ensuring coherent semantics of the data they represent. To this aim, their Pydantic type is represented by the aslot, that can be assigned and modified at runtime. 

Any subclass of BaseModel (i.e. any possible Pydantic Type) can be used as an atype as long as it is serializable.

```python
from agentics.core.agentics import Agentics as AG
from pydantic import BaseModel

class Movie(BaseModel):
    title: str
    genre: str
    description:str

movies = AG(atype=Movie)
movies.states.append(Movie(title="Superman"))
print(movies)
```

## Importing CSV and JSONL

Agentics states can be initialized loaded and saved to .csv or .jsonl files. AType will be automatically generated from the column names (after they will be normalized as needed for valid pydantic fields), with all attributes set to strings.

```python
from pydantic import BaseModel
from agentics.core.agentics import Agentics as AG


# Load CSV automatically acquiring atype
orders = AG.from_csv("data/orders.csv")

# Note that atype contains only strings.
print(orders.atype)
orders.to_csv("data/orders_copy.csv")

# Load Jsonl automatically acquiring atype. 
orders = AG.from_jsonl("data/orders.jsonl")

# Note that atype contains integers fields not only strings.
print(orders.atype)
orders.to_jsonl("data/orders_copy.jsonl")
```

If atype is provided, the file must contain fields that match the attributes defined in atype for them to be acquired, otherwise they'll be set to null. Providing explicit atype is recommedend to have more control on the types of the attributes, which will be otherwise set to string, and consistency on the column names and attribute matching. In addition, it is a convenient way to narrow down the number of attributes required for the task.



```python
# Load from CSV providing custom type (Only matching column names will be inferred)
orders = AG.from_csv("data/orders.csv", atype = Order)
print(orders.atype)

#note that states contains only the attribites in atype, others have been filtered out
print(orders.pretty_print())
AG.to_csv("data/orders_filtered.jsonl")
```

## Rebind

Agentic types are mutable, and can be modified dynamically, by assigning a new atype

```python
movies = AG.from_csv("data/orders.csv")
print(movies.atype)

class MovieReview(Movie):
    review:str
    quality_score:Optional[int] = Field(None,description="The quality of the movies in a scale 0 to 10")

movies.rebind_atype(MovieReview)
print(movies.states[0])

```

You can also modify and rebind an exiting Agentic. Similarly can also remove attributes. The following code is equivalent to the code before

```python
movies = AG.from_csv("data/orders.csv")
movies.add_attribute("review",str)
movies.add_attribute("quality_score",int,description="The quality of the movies in a scale 0 to 10")
print(movies[0])
movies.subset_atype("title","genre","description")
print(movies[0]) ## note that movies[0] is equivalent to 
```


## Reference code

[explore this example](src/agentics/examples/agentics_basics.py)


## See Next: Transduction
 
Wrapping pydantic types into Agentics provides them with the ability to perform transduction, as described in the [next section](transduction.md)
