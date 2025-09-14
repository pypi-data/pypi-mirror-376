from abc import ABC, abstractmethod
from dataclasses import dataclass
import functools
from typing import Callable, Generic, Literal, Optional, ParamSpec, Self, TypeVar, overload
from collections import deque
from hashlib import blake2b
from warnings import warn
from weakref import WeakKeyDictionary

FINGERPRINT_SIZE = 16  # bytes

Tin = TypeVar("Tin")
Tout = TypeVar("Tout")
Tkey = TypeVar("Tkey")
P = ParamSpec("P")


class cached_property(Generic[Tin, Tout, Tkey]):

    # def __init__(self, func: Callable[[Tin], Tout]):
    #     self.func = func
    #     # mapping instance id -> value
    #     self.cache: dict[int, Tout] = {}
    #     self.key = id

    def __init__(self, func: Optional[Callable[[Tin], Tout]] = None, *, 
                       key: Optional[Callable[[Tin], Tkey]] = None,
                       storage_mode: Literal["dict", "weakkey"] = "dict"):
        self._func = func
        self._storage_mode: Optional[str] = storage_mode

        if storage_mode == "weakkey" and key is None:
            # utiliser l'instance elle-même comme clé
            key = lambda obj: obj # type: ignore

        # key (default: id)
        self._key: Callable[[Tin], Tkey] = key if key is not None else id # type: ignore
        self._cache: dict[Tkey, Tout] | WeakKeyDictionary[Tkey, Tout] = {} if storage_mode == "dict" else WeakKeyDictionary()

        if func is not None:
            functools.update_wrapper(self, func)

    def __call__(self, func: Callable[[Tin], Tout]) -> 'cached_property[Tin, Tout, Tkey]':
        # support @cached_property(...) returning descriptor which is then called with func
        self._func = func
        functools.update_wrapper(self, func)
        return self

        
    def is_set(self, instance: Tin) -> bool:
        """Vérifie si la valeur du cache est déjà définie pour une instance spécifique."""
        return self._key(instance) in self._cache

    @overload
    def __get__(self, instance: None, owner) -> 'cached_property[Tin, Tout, Tkey]':
        ...
    @overload
    def __get__(self, instance: Tin, owner) -> Tout:
        ...
    def __get__(self, instance: Tin | None, owner) -> Tout | 'cached_property[Tin, Tout, Tkey]':
        if instance is None:
            return self
        if self._func is None:
            raise AttributeError("uninitialized cached_property")
        if self._key(instance) not in self._cache:
            self._cache[self._key(instance)] = self._func(instance)
        return self._cache[self._key(instance)]

    def __set__(self, instance: Tin | None, value: Tout) -> None:
        if instance is None:
            return
        if self._key(instance) in self._cache:
            raise AttributeError("Can't set read-only cached_property")
        self._cache[self._key(instance)] = value

    def set(self, instance: Tin, value: Tout) -> None:
        """
        Définit la valeur du cache manuellement pour une instance spécifique.
        Utile pour dé-récursiver des calculs.
        Raises AttributeError si la valeur est déjà définie.
        """
        self.__set__(instance, value)
    
    def clear_cache(self, instance: Optional[Tin] = None) -> None:
        """Efface le cache pour une instance spécifique ou pour toutes si instance=None."""
        if instance is None:
            self._cache.clear()
        elif self._key(instance) in self._cache:
            del self._cache[self._key(instance)]


class Node(ABC):
    __slots__ = ('__weakref__',)
    @abstractmethod
    def __repr__(self) -> str:
        pass
    
    @abstractmethod
    def _simplify(self, seen: dict['Node', 'Node']) -> 'Node':
        """
        Retourne une version simplifiée de l'arbre.
        Utilise un cache 'seen' pour éviter les recalculs.
        Le cache est un dictionnaire mapping Node -> Node simplifié.
        """
        pass

    def simplify(self) -> 'Node':
        """Retourne une version simplifiée de l'arbre."""
        return self._simplify({})
    
    @abstractmethod
    def and_(self, other: 'Node') -> 'Node':
        """
        Effectue une conjonction (ET logique) entre deux arbres.
        """
        pass

    @abstractmethod
    def or_(self, other: 'Node') -> 'Node':
        """
        Effectue une disjonction (OU logique) entre deux arbres.
        """
        pass

    @abstractmethod
    def not_(self) -> 'Node':
        """
        Effectue une négation (NON logique) de l'arbre.
        """
        pass
    
    @abstractmethod
    def vars(self) -> frozenset[str]:
        """Retourne l'ensemble des variables présentes dans l'arbre."""
        pass

    def __invert__(self) -> 'Node':
        """Opérateur de négation (~)."""
        return self.not_()
    def __or__(self, other: 'Node') -> 'Node':
        """Opérateur de disjonction (|)."""
        return self.or_(other)
    def __and__(self, other: 'Node') -> 'Node':
        """Opérateur de conjonction (&)."""
        return self.and_(other)
    
    
    @cached_property(key=lambda self: self.fingerprint) # type: ignore
    def solutions(self: Self) -> frozenset[frozenset[tuple[str, bool]]]:
        if isinstance(self, Var):
            stack = deque[tuple[Var, Literal["call", "resume"]]]()
            stack.append((self, "call")) # Si on est ici Var.solve.is_set(self) == False
            
            def call(n: Node):
                nonlocal stack
                if isinstance(n, Var) and not Node.solutions.is_set(n):
                    # On ajoute à la file d'appel seulement si pas déjà calculé
                    stack.append((n, "call"))
            
            def get_solutions(n: Node) -> frozenset[frozenset[tuple[str, bool]]]:
                if isinstance(n, Var):
                    if not Node.solutions.is_set(n):
                        # Si on est ici c'est que le cache a (sûrement) été effacé
                        warn(f"get_solutions called on unsolved node {n}")
                    return n.solutions
                elif isinstance(n, TerminalNode):
                    # True : une solution ne requierant pas de variable
                    # False : aucune solution
                    return frozenset((frozenset(),)) if n.value else frozenset()
                else:
                    raise NotImplementedError(f"solve() not implemented for {type(n)}")

            while stack:
                node, state = stack.pop()
                if Node.solutions.is_set(node):
                    continue
                if state == "call":
                    stack.append((node, "resume"))
                    call(node.true)
                    call(node.false)    
                else: # resume
                    result = frozenset()
                    if node.false == node.true:
                        # Si node.true == node.false la variable est inutile
                        # NB : On ne devrait pas être ici car un ROBDD ne peut pas avoir deux branches identiques
                        warn("Identical branches in ROBDD, variable should be eliminated")
                        result = get_solutions(node.true)
                    elif node.true == TRUE:
                        # si node.true == TRUE la variable à True est suffisante
                        # et les solutions de node.false aussi
                        result = get_solutions(node.false) | frozenset((frozenset(((node.name, True),)),))
                    elif node.false == TRUE:
                        # si node.false == TRUE la variable à False est suffisante
                        # et les solutions de node.true aussi
                        result = get_solutions(node.true) | frozenset((frozenset(((node.name, False),)),))
                    else:
                        t = get_solutions(node.true)
                        f = get_solutions(node.false)
                        T = t-f
                        F = f-t
                        if not T and not F:
                            # branches identiques: variable inutile
                            # NB : On ne devrait pas être ici car déjà géré plus haut
                            # et un ROBDD ne peut pas avoir deux branches identiques
                            result = t
                        else:
                            inter = t & f # les solutions communes n'ont pas besoin de la variable
                            # combinaisons des solutions exclusives des deux branches
                            # celles-ci n'ont pas besoin de la variable exemple : 
                            # pour (A & B) | (~A & C) : (B, C) est une solution suffisante
                            TxF = {solT | solF for solT in T for solF in F} 
                            # solutions avec la variable préfixée
                            pref_t = {frozenset({(node.name, True)}) | sol for sol in T}
                            pref_f = {frozenset({(node.name, False)}) | sol for sol in F}

                            # suppression des solutions non minimales
                            candidates = inter | pref_t | pref_f | TxF
                            result = frozenset(sol for sol in candidates
                                    if not any(o != sol and o.issubset(sol) for o in candidates))
                    
                    Node.solutions.set(node, result)
            if not Node.solutions.is_set(self):
                raise RuntimeError("Internal error: solutions not set after processing")
            return self.solutions
        elif isinstance(self, TerminalNode):
            if self.value:
                return frozenset((frozenset(),))
            else:
                return frozenset()
        else:
            raise NotImplementedError(f"solve() not implemented for {type(self)}")

    def implies(self, other: 'Node') -> bool:
        """
        Vérifie si l'arbre actuel implique un autre arbre (self => other).
        Cela équivaut à vérifier si (self AND NOT other) est insatisfaisable.
        """
        return FALSE == (self & ~other)

    @cached_property(storage_mode="weakkey")
    def fingerprint(self) -> bytes:
        """
        Calcule le fingerprint (empreinte) de l'arbre.
        Utile pour des comparaisons rapides. (plus fiable que hash)
        """
        if isinstance(self, TerminalNode):
            h = blake2b(digest_size=FINGERPRINT_SIZE)
            h.update(b'T' if self.value else b'F')
            return h.digest()
        elif isinstance(self, Var): # else
            stack = deque[tuple[Node, Literal["call", "resume"], int]]()
            results: list[bytes] = [b""] # node id -> résultat hash
            req: dict[int, int] = {}  # node id -> sous résultats indices

            stack.append((self, "call", 0)) # Si on est ici Var.hash.is_set(self) == False
            
            while stack:
                node, state, result_index = stack.pop()

                if not isinstance(node, Var) or Var.fingerprint.is_set(node):
                    results[result_index] = node.fingerprint
                    continue
                elif isinstance(node, Var): #else
                    if state == "call":
                        stack.append((node, "resume", result_index))
                        req[result_index] = len(results)
                        
                        if not isinstance(node.true, Var) or Var.fingerprint.is_set(node.true):
                            # Si pas besoin de calculer le resultat on le stock directement
                            results.append(node.true.fingerprint)
                        else:
                            # Si non on ajoute le calcul à la pile d'appel
                            stack.append((node.true, "call", len(results)))
                            results.append(b"")
                        if not isinstance(node.false, Var) or Var.fingerprint.is_set(node.false):
                            results.append(node.false.fingerprint)
                        else:
                            stack.append((node.false, "call", len(results)))
                            results.append(b"")

                    elif state == "resume" and isinstance(node, Var): # state==resume => isinstance(node, Var) -> type hinter
                        if not Var.fingerprint.is_set(node):
                            h = blake2b(digest_size=FINGERPRINT_SIZE)
                            h.update(b'V')
                            h.update(node.name.encode())
                            # On recupère les resultats
                            h.update(results[req[result_index]])
                            h.update(results[req[result_index] + 1])
                            # On calcul le hash,on le met à jour manuellement et on le stock dans result
                            calculated = h.digest()
                            Var.fingerprint.set(node, calculated)
                            results[result_index] = calculated
                        else:
                            results[result_index] = node.fingerprint
                else:
                    raise NotImplementedError(f'Unexpected node of type {type(node).__name__}')
            return results[0]
        raise NotImplementedError(f"fingerprint() not implemented for {type(self)}")

    @cached_property
    def hash(self) -> int:
        # /!\ Risque de collision élevé utiliser fingerprint si possible
        # Utilisation d'une pile (node, etat, result_index)
        # etat = call -> resume, call(true, len(results)), call(false, len(result)+1)
        #        resume -> store Hash(node.name, )
        stack = deque[tuple[Node, Literal["call", "resume"], int]]()
        results: list[int|None] = [None] # node id -> résultat hash
        req: dict[int, int] = {}  # node id -> sous résultats indices

        stack.append((self, "call", 0)) # Si on est ici Var.hash.is_set(self) == False
        
        while stack:
            node, state, result_index = stack.pop()

            if not isinstance(node, Var) or Var.hash.is_set(node):
                results[result_index] = hash(node)
                continue
            elif isinstance(node, Var): #else
                if state == "call":
                    stack.append((node, "resume", result_index))
                    req[result_index] = len(results)
                    
                    if not isinstance(node.true, Var) or Var.hash.is_set(node.true):
                        # Si pas besoin de calculer le resultat on le stock directement
                        results.append(hash(node.true))
                    else:
                        # Si non on ajoute le calcul à la pile d'appel
                        stack.append((node.true, "call", len(results)))
                        results.append(None)
                    if not isinstance(node.false, Var) or Var.hash.is_set(node.false):
                        results.append(hash(node.false))
                    else:
                        stack.append((node.false, "call", len(results)))
                        results.append(None)

                elif state == "resume" and isinstance(node, Var): # state==resume => isinstance(node, Var) -> type hinter
                    if not Var.hash.is_set(node):
                        # On recupère les resultats
                        true_res = results[req[result_index]]
                        false_res = results[req[result_index] + 1]
                        # On calcul le hash,on le met à jour manuellement et on le stock dans result
                        calculated = hash((node.name, true_res, false_res))
                        Var.hash.set(node, calculated)
                        results[result_index] = calculated
                    else:
                        results[result_index] = hash(node)
            else:
                raise NotImplementedError(f'Unexpected node of type {type(node).__name__}')
        return results[0] # type: ignore
    
    def __hash__(self) -> int:
        return self.hash

    @abstractmethod
    def eval(self, env: dict[str, bool]) -> bool:
        """
        Évalue l'arbre pour un environnement donné (mapping variable -> booléen).
        Retourne True si l'arbre est satisfait, False sinon (contradiction ou inconnu).
        """
        pass

    @abstractmethod
    def fix(self, env: dict[str, bool]) -> 'Node':
        """
        Retourne un nouvel arbre où les variables dans env sont fixées aux valeurs données.
        """
        pass

    def print(self, use_color: bool = True, use_ref: bool = True) -> None:
        """
        Affiche l'arbre.
        use_color : active les couleurs ANSI si possible.
        use_ref   : si True, les sous-arbres expansibles réutilisés sont remplacés par une référence (#n / #n↩).
                    si False, l'arbre est entièrement développé et aucun identifiant n'est affiché.
        """
        # Fonction générée automatiquement
        # Détecte si un nœud (VarNode) est expansible (non trivial)
        def expandable(node: 'Node') -> bool:
            return isinstance(node, Var) and not (
                (node.true == TRUE and node.false == FALSE) or
                (node.true == FALSE and node.false == TRUE)
            )

        # Comptage des occurrences uniquement si on veut les références
        if use_ref:
            counts: dict[Node, int] = {}
            def count(node: 'Node'):
                if isinstance(node, TerminalNode) or not expandable(node):
                    return
                counts[node] = counts.get(node, 0) + 1
                if counts[node] == 1:  # Descend seulement la première fois
                    count(node.true)   # type: ignore
                    count(node.false)  # type: ignore
            count(self)
            reused = {n for n, c in counts.items() if c > 1}
        else:
            reused = set()

        # Détection support couleurs
        if use_color:
            try:
                import sys, os
                use_color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
            except Exception:
                use_color = False

        # Codes ANSI
        if use_color:
            RESET = "\x1b[0m"
            DIM = "\x1b[2m"
            CYAN = "\x1b[36m"
            YELLOW = "\x1b[33m"
            GREEN = "\x1b[32m"
            RED = "\x1b[31m"
            MAGENTA = "\x1b[35m"
            WHITE = "\x1b[37m"
        else:
            RESET = DIM = CYAN = YELLOW = GREEN = RED = MAGENTA = WHITE = ""

        def color_edge(tag: str) -> str:
            if tag == "T":
                return f"{GREEN}{tag}{RESET}" if use_color else tag
            if tag == "F":
                return f"{RED}{tag}{RESET}" if use_color else tag
            return tag

        def label(node: 'Node') -> str:
            if isinstance(node, TerminalNode):
                return (f"{GREEN}TRUE{RESET}" if (use_color and node.value)
                        else f"{RED}FALSE{RESET}" if (use_color and not node.value)
                        else ("TRUE" if node.value else "FALSE"))
            if isinstance(node, Var):
                if node.true == TRUE and node.false == FALSE:
                    return f"{YELLOW}{node.name}{RESET}" if use_color else node.name
                if node.true == FALSE and node.false == TRUE:
                    txt = f"!{node.name}"
                    return f"{YELLOW}{txt}{RESET}" if use_color else txt
                return f"{CYAN}{node.name}{RESET}" if use_color else node.name
            return repr(node)

        lines: list[str] = []
        reused_ids: dict[Node, int] = {}
        next_id = 1

        def visit(node: 'Node', prefix: str = "", is_last: bool = True,
                  edge: Optional[str] = None, is_root: bool = False):
            nonlocal next_id
            conn_raw = "" if is_root else ("└── " if is_last else "├── ")
            conn = f"{DIM}{conn_raw}{RESET}" if (use_color and not is_root) else conn_raw
            edge_txt = f"{color_edge(edge)}: " if edge is not None else ""
            is_expandable = expandable(node)

            id_part = ""
            repeated = False
            if use_ref and is_expandable and node in reused:
                if node in reused_ids:
                    repeated = True
                    idx = reused_ids[node]
                else:
                    reused_ids[node] = next_id
                    idx = next_id
                    next_id += 1
                if repeated:
                    id_part = f" {MAGENTA}#{idx}↩{RESET}" if use_color else f" #{idx}↩"
                else:
                    id_part = f" {WHITE}#{idx}{RESET}" if use_color else f" #{idx}"

            lines.append(f"{prefix}{conn}{edge_txt}{label(node)}{id_part}")

            if not is_expandable or (use_ref and repeated):
                return

            child_prefix = prefix + ("" if is_root else ("    " if is_last else "│   "))
            if use_color and not is_root:
                child_prefix = child_prefix.replace("│", f"{DIM}│{RESET}")

            # type: ignore because node.true / node.false only exist for VarNode
            visit(node.true, child_prefix, False, "T", False)  # type: ignore
            visit(node.false, child_prefix, True, "F", False)  # type: ignore

        visit(self, is_root=True)
        print("\n".join(lines))

    def print_table(self, solutions_only: bool = False, use_color: bool = True) -> None:
        vars = sorted(self.vars())
        n = len(vars)

        # Couleurs ANSI (optionnelles)
        if use_color:
            try:
                import sys, os
                use_color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
            except Exception:
                use_color = False
        if use_color:
            RESET = "\x1b[0m"
            GREEN = "\x1b[32m"
            RED = "\x1b[31m"
            YELLOW = "\x1b[33m"
        else:
            RESET = GREEN = RED = YELLOW = ""

        if n == 0: # pas de variables = TerminalNode
            if self == TRUE:
                print(f"Résultat: {GREEN}1{RESET}")
            else:
                print(f"Résultat: {RED}0{RESET}")
            return

        # Variables nécessaires: toutes les solutions spécifient la même valeur pour v
        necessary: dict[str, str | None] = {}
        if self.solutions:
            for v in vars:
                vals = [dict(sol).get(v) for sol in self.solutions]
                if any(val is None for val in vals):
                    necessary[v] = None
                else:
                    all_true = all(val is True for val in vals)
                    all_false = all(val is False for val in vals)
                    necessary[v] = 'T' if all_true else ('F' if all_false else None)
        else:
            necessary = {v: None for v in vars}

        # En-tête (variables colorées si nécessaires)
        def color_var_header(v: str) -> str:
            if necessary.get(v) == 'T':
                return f"{GREEN}{v}{RESET}"
            if necessary.get(v) == 'F':
                return f"{RED}{v}{RESET}"
            return v

        header = " | ".join(color_var_header(v) for v in vars) + " | Résultat"
        print(header)
        print("-" * (4 * n + 10))

        if solutions_only:
            # Repérer la/les solutions avec le moins de contraintes
            min_len = min((len(sol) for sol in self.solutions), default=0)
            for sol in self.solutions:
                sol_dict = dict(sol)
                parts: list[str] = []
                for v in vars:
                    if v in sol_dict:
                        parts.append((GREEN + "1" + RESET) if sol_dict[v] else (RED + "0" + RESET))
                    else:
                        parts.append("*")
                # Résultat coloré en jaune si solution de longueur minimale
                res = (YELLOW + "1" + RESET) if len(sol) == min_len else "1"
                print(" | ".join(parts) + f" |   {res}")
        else:
            for i in range(2 ** n):
                values = [(vars[j], bool((i >> (n - j - 1)) & 1)) for j in range(n)]
                env = dict(values)
                # Evaluation de l'arbre
                result = self.eval(env)
                if result:
                    parts = [GREEN + ("1" if env[v] else "0") + RESET for v in vars]
                    res = GREEN + "1" + RESET
                else:
                    parts = ["1" if env[v] else "0" for v in vars]
                    res = RED + "0" + RESET
                print(" | ".join(parts) + f" |   {res}")
    
    def __str__(self) -> str:
        if isinstance(self, TerminalNode):
            return "TRUE" if self.value else "FALSE"
        else:
            result = []
            for sol in self.solutions:
                result.append("(" + " & ".join((f"!{var}" if not val else var) for var, val in sorted(sol)) + ")")
            return "|".join(result)
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Node):
            return NotImplemented
        return self is other or self.fingerprint == other.fingerprint


@dataclass(frozen=True, slots=True)
class TerminalNode(Node):
    value: bool

    def __repr__(self) -> str:
        return "TRUE" if self.value else "FALSE"
    def _simplify(self, seen: dict['Node', 'Node']) -> Node:
        # Déjà simplifié
        return self
    def and_(self, other: Node) -> Node:
        # TRUE & X = X ; FALSE & X = FALSE
        return other if self.value else self
    def or_(self, other: Node) -> Node:
        # TRUE | X = TRUE ; FALSE | X = X
        return self if self.value else other
    def not_(self) -> Node:
        # not TRUE = FALSE ; not FALSE = TRUE
        return FALSE if self.value else TRUE
    def vars(self) -> frozenset[str]:
        # Pas de variables
        return frozenset()
    
    # @cached_generator
    # def solve(self) -> Generator[tuple[tuple[str, bool], ...]]:
    #    # Cas terminal
    #    if self.value:
    #        yield ()
    def eval(self, env: dict[str, bool]) -> bool:
        return self.value
    
    def fix(self, env: dict[str, bool]) -> Node:
        return self


TRUE = TerminalNode(True)
FALSE = TerminalNode(False)


@dataclass(frozen=True, slots=True)
class Var(Node):
    name: str
    true: Node = TRUE
    false: Node = FALSE

    def __repr__(self) -> str:
        if self.true == TRUE and self.false == FALSE:
            return self.name
        elif self.true == FALSE and self.false == TRUE:
            return f"!{self.name}"
        return f"({self.name})?({self.true!r}):({self.false!r})"
    
    def _simplify(self, seen: dict['Node', 'Node']) -> Node:
        if self in seen:
            return seen[self]
        if self.true == self.false:
            seen[self] = self.true
            return self.true
        t = self.true._simplify(seen)
        f = self.false._simplify(seen)
        if t == f:
            seen[self] = t
            return t
        if t != self.true or f != self.false:
            result = Var(self.name, t, f)
            seen[self] = result
            seen[result] = result
            return result
        seen[self] = self
        return self

    def _op(self, other: Node, op: Literal["and", "or"]) -> Node:
        if self == other:
            return self
        
        # Utilisation d'une pile (self, other, etat)
        # avec self < other 
        # etat = call -> resume, call(true), call(false)
        #        resume -> store VarNode(self.name, result_true, result_false)
        stack = deque[tuple[Node, Node, Literal["call", "resume"]]]()
        results: dict[tuple[Node, Node], Node] = {}   # order(self, other) -> résultat

        def order(a: Node, b: Node) -> tuple[Node,Node]:
            if isinstance(a, TerminalNode) and isinstance(b, TerminalNode):
                return (a,b) if a.value < b.value else (b,a)
            if isinstance(a, TerminalNode):
                return (a, b)
            if isinstance(b, TerminalNode):
                return (b, a)
            if isinstance(a, Var) and isinstance(b, Var):
                return (a, b) if a.name < b.name else (b, a)
            raise NotImplementedError(f'Unexpected nodes of type {type(a).__name__} and {type(b).__name__}')
        
        stack.append((*order(self, other), "call"))
        
        while stack:
            self, other, state = stack.pop()

            if self == other:
                results[(self, other)] = self
                continue

            if isinstance(self, TerminalNode):
                if op == "and":
                    results[(self, other)] = self.and_(other)
                else:
                    results[(self, other)] = self.or_(other)
                continue
            elif isinstance(self, Var) and isinstance(other, Var): #else
                # Si déjà calculé → pas besoin de refaire
                if (self, other) in results:
                    continue
                
                if state == "call":
                    stack.append((self, other, "resume"))
                    if self.name == other.name:
                        if (cpl := order(self.true, other.true)) not in results:
                            stack.append((*cpl, "call"))
                        if (cpl := order(self.false, other.false)) not in results:
                            stack.append((*cpl, "call"))
                    else: # self.name < other.name
                        if (cpl := order(self.true, other)) not in results:
                            stack.append((*cpl, "call"))
                        if (cpl := order(self.false, other)) not in results:
                            stack.append((*cpl, "call"))

                elif state == "resume":
                    if self.name == other.name:
                        true_res = results[order(self.true, other.true)]
                        false_res = results[order(self.false, other.false)]
                    else: # self.name < other.name
                        true_res = results[order(self.true, other)]
                        false_res = results[order(self.false, other)]
                    results[(self, other)] = Var(self.name, true_res, false_res)
            else:
                raise NotImplementedError(f'Unexpected node pair of type ({type(self).__name__}, {type(other).__name__})')

        return results[(self, other)].simplify()

    def and_(self, other: Node) -> Node:
        return self._op(other, "and")
    
    def or_(self, other: Node) -> Node:
        return self._op(other, "or")
    
    def __hash__(self) -> int:
        return self.hash

    def not_(self) -> Node:
        # Utilisation d'une pile (node, etat)
        # etat = call -> resume, call(true), call(false)
        #        resume -> store VarNode(self.name, result_true, result_false)
        stack = deque[tuple[Node, Literal["call", "resume"]]]()
        results: dict[Node, Node] = {}   # node -> resultat

        stack.append((self, "call"))
        
        while stack:
            node, state = stack.pop()

            if isinstance(node, TerminalNode):
                results[node] = node.not_()
                continue
            elif isinstance(node, Var): #else
                # Si déjà calculé -> pas besoin de refaire
                if node in results:
                    continue
                
                if state == "call":
                    stack.append((node, "resume"))
                    if (node.true not in results):
                        stack.append((node.true, "call"))
                    if (node.false not in results):
                        stack.append((node.false, "call"))

                elif state == "resume":
                    true_res = results[node.true]
                    false_res = results[node.false]
                    results[node] = Var(node.name, true_res, false_res)
            else:
                raise NotImplementedError(f'Unexpected node of type {type(node).__name__}')

        return results[self].simplify() # type: ignore
    
    def vars(self) -> frozenset[str]:
        return frozenset({self.name}) | self.true.vars() | self.false.vars()

    def eval(self, env: dict[str, bool]) -> bool:
        if self.name in env:
            return self.true.eval(env) if env[self.name] else self.false.eval(env)
        else:
            t = self.true.eval(env)
            f = self.false.eval(env)
            return True == t == f

    def fix(self, env: dict[str, bool]) -> Node:
        """
        Retourne un nouvel arbre où les variables dans env sont fixées aux valeurs données.
        """
        if self.name in env:
            return self.true.fix(env) if env[self.name] else self.false.fix(env)
        else:
            t = self.true.fix(env) if isinstance(self.true, Var) else self.true
            f = self.false.fix(env) if isinstance(self.false, Var) else self.false
            if t == f:
                return t
            if t != self.true or f != self.false:
                return Var(self.name, t, f)
            return self

