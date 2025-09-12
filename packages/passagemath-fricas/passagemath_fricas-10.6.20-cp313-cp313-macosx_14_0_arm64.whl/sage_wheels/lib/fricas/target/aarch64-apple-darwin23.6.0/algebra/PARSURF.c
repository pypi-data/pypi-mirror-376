/*      Compiler: ECL 24.5.10                                         */
/*      Date: 2025/9/11 09:26 (yyyy/mm/dd)                            */
/*      Machine: Darwin 23.6.0 arm64                                  */
/*      Source: /Users/runner/sage-local/var/tmp/sage/build/fricas-1.3.12/src/pre-generated/src/algebra/PARSURF.lsp */
#include <ecl/ecl-cmp.h>
#include "/Users/runner/sage-local/var/tmp/sage/build/fricas-1.3.12/src/_build/target/aarch64-apple-darwin23.6.0/algebra/PARSURF.eclh"
/*      function definition for PARSURF;surface;3ComponentFunction%;1 */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L326_parsurf_surface_3componentfunction__1_(cl_object v1_x_, cl_object v2_y_, cl_object v3_z_, cl_object v4_)
{
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 value0 = cl_vector(3, v1_x_, v2_y_, v3_z_);
 return value0;
}
/*      function definition for PARSURF;coordinate;%NniComponentFunction;2 */
/*      optimize speed 3, debug 0, space 0, safety 0                  */
static cl_object L327_parsurf_coordinate__nnicomponentfunction_2_(cl_object v1_c_, cl_object v2_n_, cl_object v3_)
{
 cl_object env0 = ECL_NIL;
 const cl_env_ptr cl_env_copy = ecl_process_env();
 cl_object value0;
TTL:
 if (!((v2_n_)==(ecl_make_fixnum(1)))) { goto L1; }
 value0 = (v1_c_)->vector.self.t[0];
 cl_env_copy->nvalues = 1;
 return value0;
L1:;
 if (!((v2_n_)==(ecl_make_fixnum(2)))) { goto L3; }
 value0 = (v1_c_)->vector.self.t[1];
 cl_env_copy->nvalues = 1;
 return value0;
L3:;
 if (!((v2_n_)==(ecl_make_fixnum(3)))) { goto L5; }
 value0 = (v1_c_)->vector.self.t[2];
 cl_env_copy->nvalues = 1;
 return value0;
L5:;
 value0 = ecl_function_dispatch(cl_env_copy,VV[16])(1, VV[3]) /*  error */;
 return value0;
}