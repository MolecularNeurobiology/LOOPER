#ifndef R_PCC_H
#define R_PCC_H

enum EState {
  E_IDLE,
  E_S2_B,
  E_S1_1,
  E_S2_F,
  E_V,
  E_C,
};

enum PState {
  P_IDLE,
  P_PAUSE,
  P_S2_B,
  P_S1_HOME,
  P_S1_OUT,
  P_S2_F,
};

extern EState estate;
extern PState pstate;

#endif