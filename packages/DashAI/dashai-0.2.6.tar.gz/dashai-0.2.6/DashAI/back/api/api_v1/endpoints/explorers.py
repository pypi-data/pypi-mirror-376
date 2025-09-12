import logging
import pathlib

from beartype.typing import List
from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from kink import di, inject
from sqlalchemy import exc
from sqlalchemy.orm import Session, sessionmaker

from DashAI.back.api.api_v1.schemas import explorers_params as schemas
from DashAI.back.core.enums.status import ExplorerStatus
from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec
from DashAI.back.dependencies.database.models import Dataset, Explorer, Notebook
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.exploration.base_explorer import BaseExplorer

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

router = APIRouter()

# Validations


def validate_explorer_params(
    session: Session,
    component_registry: ComponentRegistry,
    explorer: Explorer,
    validate_columns: bool = True,
):
    """
    Function to validate explorer parameters.
    It validates:
    - The `exploration_type` against the registered explorers.
    - The `parameters` against the explorer schema.
    - The `dataset_id` and `columns` against the dataset.
    """
    # validate exploration_type in registered explorers
    if explorer.exploration_type not in component_registry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exploration type {explorer.exploration_type} not found",
        )

    # validate parameters with class method
    explorer_class: BaseExplorer = component_registry[explorer.exploration_type][
        "class"
    ]
    try:
        valid = explorer_class.validate_parameters(explorer.parameters)
    except Exception as e:
        log.exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error while validating explorer parameters",
        ) from e

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parameters for the explorer",
        )

    # validate dataset_id and columns against dataset
    notebook = session.query(Notebook).get(explorer.notebook_id)
    if notebook is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notebook not found",
        )

    dataset = session.query(Dataset).get(notebook.dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found",
        )

    if validate_columns:
        # validate columns against dataset columns
        dataset_path = f"{notebook.file_path}/dataset"
        columns_spec = get_columns_spec(dataset_path)

        try:
            explorer_class.validate_columns(explorer, columns_spec)
        except Exception as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error while validating explorer columns",
            ) from e

    return True


def validate_explorer_finished(explorer: Explorer):
    """
    Function to validate if the explorer is finished.
    """
    if explorer.status != ExplorerStatus.FINISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explorer is not finished",
        )

    if (
        explorer.exploration_path is None
        or explorer.exploration_path == ""
        or not pathlib.Path(explorer.exploration_path).exists()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exploration path not found",
        )

    return True


# GET
@router.get("/", response_model=List[schemas.Explorer])
@inject
async def get_explorers(
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    skip: int = 0,
    limit: int = 0,
):
    db: Session
    with session_factory() as db:
        explorers = db.query(Explorer)

        if skip > 0:
            explorers = explorers.offset(skip)
        if limit > 0:
            explorers = explorers.limit(limit)

        return explorers.all()


@router.get("/{explorer_id}/", response_model=schemas.Explorer)
@inject
async def get_explorer_by_id(
    explorer_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    db: Session
    with session_factory() as db:
        explorer = db.query(Explorer).get(explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )
        return explorer


@router.get("/exploration/{exploration_id}/", response_model=List[schemas.Explorer])
@inject
async def get_explorers_by_exploration_id(
    exploration_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    skip: int = 0,
    limit: int = 0,
):
    db: Session
    with session_factory() as db:
        explorers = db.query(Explorer).filter(Explorer.exploration_id == exploration_id)

        if skip > 0:
            explorers = explorers.offset(skip)
        if limit > 0:
            explorers = explorers.limit(limit)

        return explorers.all()


# CREATE
@router.post("/", response_model=schemas.Explorer, status_code=status.HTTP_201_CREATED)
@inject
async def create_explorer(
    params: schemas.ExplorerCreate,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
):
    db: Session
    with session_factory() as db:
        explorer = Explorer(**params.model_dump())
        validate_explorer_params(
            session=db, component_registry=component_registry, explorer=explorer
        )

        db.add(explorer)
        db.commit()
        db.refresh(explorer)
        return explorer


# UPDATE
@router.patch("/{explorer_id}/", response_model=schemas.Explorer)
@inject
async def update_explorer(
    explorer_id: int,
    params: schemas.ExplorerBase,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
):
    db: Session
    with session_factory() as db:
        explorer = db.query(Explorer).get(explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )

        params_dict = params.model_dump()
        for key, value in params_dict.items():
            setattr(explorer, key, value)

        validate_explorer_params(
            session=db,
            component_registry=component_registry,
            explorer=explorer,
            validate_columns=False,
        )

        db.commit()
        db.refresh(explorer)
        return explorer


# DELETE
@router.delete("/{explorer_id}/")
@inject
async def delete_explorer(
    explorer_id: int,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
):
    db: Session
    with session_factory() as db:
        explorer = db.query(Explorer).get(explorer_id)
        if explorer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Explorer not found",
            )
        db.delete(explorer)
        explorer.delete_result()

        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)


# Obtain results
@router.post("/{explorer_id}/results/")
@inject
async def get_explorer_results(
    explorer_id: int,
    params: schemas.ExplorerResultsOptions,
    session_factory: sessionmaker = Depends(lambda: di["session_factory"]),
    component_registry: ComponentRegistry = Depends(lambda: di["component_registry"]),
):
    db: Session
    with session_factory() as db:
        try:
            explorer_info = db.query(Explorer).get(explorer_id)
            if explorer_info is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Explorer with id {explorer_id} not found",
                )
        except exc.SQLAlchemyError as e:
            log.exception(e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error while loading the explorer info",
            ) from e

    # validate explorer status and result path
    validate_explorer_finished(explorer=explorer_info)

    # get explorer class
    try:
        explorer_component_class = component_registry[explorer_info.exploration_type][
            "class"
        ]
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{explorer_info.exploration_type} not found in registry",
        ) from e

    # instantiate explorer class (it handles returning the results as response object)
    try:
        explorer_instance: BaseExplorer = explorer_component_class(
            **explorer_info.parameters,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error while instantiating explorer class",
        ) from e

    # get results
    try:
        results = explorer_instance.get_results(
            exploration_path=explorer_info.exploration_path,
            options=params.model_dump().get("options", {}),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error while getting explorer results",
        ) from e

    return results
