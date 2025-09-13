#include "asgard_test_macros.hpp"

using namespace asgard;

template<typename TestType>
void test_transform()
{
  current_test<TestType> name_("fast-transform");
  std::minstd_rand park_miller(42);
  std::uniform_real_distribution<TestType> unif(-1.0, 1.0);

  for (int nbatch = 1; nbatch < 5; nbatch++) {
    for (int level = 0; level < 5; level++) {
      for (int degree = 0; degree < 4; degree++)
      {
        hierarchy_manipulator<TestType> hier(degree, 1, {-2,}, {1,}); // dims 1

        int const pdof    = (degree + 1);
        int64_t const num = fm::ipow2(level);

        std::vector<TestType> ref(nbatch * num * pdof);
        std::vector<TestType> hp(nbatch * num * pdof);

        for (auto &x : ref)
          x = unif(park_miller);

        std::vector<TestType> fp(num * pdof);
        for (int b : indexof(nbatch)) // forward project
        {
          TestType *r = ref.data() + b * pdof; // batch begin
          for (int i : indexof(num))
            std::copy_n(r + i * nbatch * pdof, pdof, fp.data() + i * pdof);

          hier.project1d(level, fp); // to hierarchical

          TestType *h = hp.data() + b * pdof; // write out in hp
          for (int i : indexof(num))
            std::copy_n(fp.data() + i * pdof, pdof, h + i * nbatch * pdof);
        }

        if (level > 0)
          tassert(fm::diff_inf(ref, hp) > 1.E-2); // sanity check, did we transform anything

        hier.reconstruct1d(nbatch, level, span2d<TestType>(pdof, nbatch * num, hp.data()));

        tassert(fm::diff_inf(ref, hp) < 5.E-6); // inverse transform should get us back
      }
    }
  }
}

template<typename P>
void all_templated_tests()
{
  test_transform<P>();
}

int main(int argc, char **argv)
{
  libasgard_runtime running_(argc, argv);

  all_tests global_("transformation-tests", " hierarchical<->cell-by-cell basis");

  #ifdef ASGARD_ENABLE_DOUBLE
  all_templated_tests<double>();
  #endif

  #ifdef ASGARD_ENABLE_FLOAT
  all_templated_tests<float>();
  #endif

  return 0;
}
