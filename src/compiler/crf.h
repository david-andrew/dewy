#ifndef CRF_H
#define CRF_H

#include <stdbool.h>
#include <stdint.h>

#include "object.h"
#include "set.h"
#include "slice.h"
#include "slot.h"

// Call Return Forest data structure used by CNP parsing algorithm

typedef struct
{
    uint64_t head_idx;
    uint64_t j;
} crf_cluster_node; // nodes of the form (X, j)

typedef struct
{
    slot label;
    uint64_t j;
} crf_label_node; // nodes of the form (X ::= α•β, j)

typedef struct
{
    uint64_t cluster_node_idx;
    uint64_t label_node_idx;
} crf_edge;

typedef struct
{
    set* cluster_nodes; // set<cluster_nodes>
    set* label_nodes;   // set<label_nodes>
    set* edges;         // set<edge>
} crf;

crf* new_crf();
void crf_free(crf* CRF);
void crf_str(crf* CRF);
crf_cluster_node* crf_new_cluster_node(uint64_t head_idx, uint64_t j);
crf_cluster_node crf_cluster_node_struct(uint64_t head_idx, uint64_t j);
obj* crf_cluster_node_obj(crf_cluster_node* node);
bool crf_cluster_node_equals(crf_cluster_node* left, crf_cluster_node* right);
uint64_t crf_cluster_node_hash(crf_cluster_node* node);
void free_crf_cluster_node(crf_cluster_node* node);
void crf_cluster_node_str(crf_cluster_node* node);
void crf_cluster_node_repr(crf_cluster_node* node);
crf_label_node* crf_new_label_node(slot label, uint64_t j);
crf_label_node crf_label_node_struct(slot label, uint64_t j);
obj* crf_label_node_obj(crf_label_node* node);
bool crf_label_node_equals(crf_label_node* left, crf_label_node* right);
uint64_t crf_label_node_hash(crf_label_node* node);
void free_crf_label_node(crf_label_node* node);
void crf_label_node_str(crf_label_node* node);
void crf_label_node_repr(crf_label_node* node);
crf_edge* crf_new_edge(uint64_t cluster_node_idx, uint64_t label_node_idx);
crf_edge crf_edge_struct(uint64_t cluster_node_idx, uint64_t label_node_idx);
obj* crf_edge_obj(crf_edge* edge);
bool crf_edge_equals(crf_edge* left, crf_edge* right);
uint64_t crf_edge_hash(crf_edge* edge);
void free_crf_edge(crf_edge* edge);
void crf_edge_str(crf_edge* edge);
void crf_edge_repr(crf_edge* edge);

#endif