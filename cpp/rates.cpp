#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>

using namespace std;

double discount_factor(double interest_rate, double maturity) {
    if (maturity >= 0.0) {
        return exp(-interest_rate * maturity);
    }
    throw invalid_argument("Maturity must be at least 0");
}

double forward_rate(double rate_1, double mat_1, double rate_2, double mat_2) {
    if (mat_2 < 0.0 || mat_1 < 0.0) {
        throw invalid_argument("Maturities must be positive");
    }
    if (mat_1 == mat_2) {
        throw invalid_argument("Maturities must be different");
    }
    if (mat_1 > mat_2) {
        throw invalid_argument("Maturity 2 must be bigger than Maturity 1");
    }
    return (rate_2 * mat_2 - rate_1 * mat_1) / (mat_2 - mat_1);
}

double interpolate_zero_rate(
    const vector<double>& mats,
    const vector<double>& zeros,
    double t
) {
    if (mats.size() != zeros.size() || mats.size() < 2) {
        throw invalid_argument("Need matching maturity/zero arrays of length >= 2");
    }
    if (t <= mats.front()) {
        return zeros.front();
    }
    if (t >= mats.back()) {
        return zeros.back();
    }
    for (size_t i = 0; i + 1 < mats.size(); ++i) {
        if (t >= mats[i] && t <= mats[i + 1]) {
            double w = (t - mats[i]) / (mats[i + 1] - mats[i]);
            return zeros[i] * (1.0 - w) + zeros[i + 1] * w;
        }
    }
    throw runtime_error("Interpolation failed");
}

double price_coupon_bond(
    const vector<double>& mats,
    const vector<double>& zeros,
    double maturity,
    double coupon_rate,
    double face = 100.0,
    int frequency = 2
) {
    int n = static_cast<int>(lround(maturity * frequency));
    if (n < 1) {
        throw invalid_argument("Maturity too short for the coupon frequency");
    }
    double cpn = face * coupon_rate / frequency;
    double pv = 0.0;
    for (int i = 1; i <= n; ++i) {
        double t = static_cast<double>(i) / frequency;
        double z = interpolate_zero_rate(mats, zeros, t);
        double df = discount_factor(z, t);
        pv += cpn * df;
        if (i == n) {
            pv += face * df;
        }
    }
    return pv;
}

int main() {
    cout << "DF(4%, 2y) = " << discount_factor(0.04, 2.0) << "\n";
    cout << "Fwd(4% @2y, 4.5% @3y) = "
         << forward_rate(0.04, 2.0, 0.045, 3.0) << "\n";

    vector<double> mats = {0.5, 1.0, 2.0, 5.0, 10.0, 15.0};
    vector<double> zeros = {0.038, 0.039, 0.040, 0.041, 0.042, 0.0425};
    double px = price_coupon_bond(mats, zeros, 10.0, 0.04);
    cout << "10y 4% bond price = " << px << "\n";
    return 0;
}
